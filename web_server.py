"""
web_server.py  —  Intérprete LSP — Servidor de procesamiento MediaPipe

Arquitectura:
  - El celular/dispositivo captura vídeo con su propia cámara (getUserMedia)
  - Envía frames JPEG al endpoint POST /process_frame
  - Esta laptop SOLO procesa con MediaPipe y devuelve el frame anotado + keypoints
  - No se usa ni se comparte la cámara del laptop en absoluto

Uso:
    .\\venv_lsp\\Scripts\\python.exe web_server.py
    .\\venv_lsp\\Scripts\\python.exe web_server.py --port 5000
"""

import sys
import argparse
import base64
import threading
import os
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("OPENCV_IO_MAX_IMAGE_PIXELS", str(1280 * 720))
import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, Response, render_template_string, jsonify, request

import config.settings as settings
from src.backend.frame_api import ApiError, register_frame_api
from src.backend.sessions import SessionManager, register_sessions
from src.inference.engine import InferenceEngine, load_predictor
from src.inference.pipeline import TranslationPipeline

app = Flask(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# DETECTOR MEDIAPIPE
# ══════════════════════════════════════════════════════════════════════════════
class HandDetector:
    NUM_LANDMARKS = 21
    COORDS        = 3
    DIM           = NUM_LANDMARKS * COORDS   # 63 por mano, 126 total

    def __init__(self):
        _mp = mp.solutions.hands
        self._mp          = _mp
        self._drawing     = mp.solutions.drawing_utils
        self._draw_styles = mp.solutions.drawing_styles
        self.hands = _mp.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
        )

    def process(self, bgr: np.ndarray):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = self.hands.process(rgb)
        rgb.flags.writeable = True
        return res

    def draw(self, frame: np.ndarray, results) -> np.ndarray:
        if results.multi_hand_landmarks:
            for lm in results.multi_hand_landmarks:
                self._drawing.draw_landmarks(
                    frame, lm, self._mp.HAND_CONNECTIONS,
                    self._draw_styles.get_default_hand_landmarks_style(),
                    self._draw_styles.get_default_hand_connections_style(),
                )
        return frame

    def meta(self, results) -> list:
        info = []
        if results.multi_handedness:
            for h in results.multi_handedness:
                c = h.classification[0]
                info.append({
                    "label":    c.label,
                    "label_es": "Izquierda" if c.label == "Left" else "Derecha",
                    "confidence": round(c.score * 100, 1),
                })
        return info

    def keypoints(self, results) -> list:
        left  = np.zeros(self.DIM, dtype=np.float32)
        right = np.zeros(self.DIM, dtype=np.float32)
        if results.multi_hand_landmarks and results.multi_handedness:
            for lm, hd in zip(results.multi_hand_landmarks, results.multi_handedness):
                pts = np.array(
                    [[p.x, p.y, p.z] for p in lm.landmark], dtype=np.float32
                ).flatten()
                if hd.classification[0].label == "Left":
                    left = pts
                else:
                    right = pts
        return np.concatenate([left, right]).tolist()


# Instancia global + lock (serializa acceso entre múltiples clientes)
_detector      = None
_detector_lock = threading.Lock()


# ══════════════════════════════════════════════════════════════════════════════
# HTML  —  interfaz para el dispositivo cliente
# ══════════════════════════════════════════════════════════════════════════════
_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LSP — Detección de Manos</title>
<link rel="stylesheet" href="/static/styles.css"/>
</head>
<body data-state="Idle" data-model-ready="{{ 'true' if model_ready else 'false' }}">

<header>
  <div class="logo">🤟</div>
  <div>
    <h1>Demo LSP: detección de manos</h1>
    <p>Tu cámara · Procesado por MediaPipe</p>
  </div>
  <div class="pill" id="live-pill" style="display:none">
    <div class="dot"></div> Procesando
  </div>
</header>

<!-- VIDEO -->
<main class="console-shell">
<div class="video-section">
  <video id="local-video" playsinline autoplay muted style="display:none"></video>
  <img id="processed-img"
    src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
    alt="Vista de la cámara con puntos de manos detectados"/>

  <div id="lat-badge">Latencia: <span id="lat-val">—</span> ms</div>
  <button id="btn-flip" title="Cambiar cámara" aria-label="Cambiar cámara">🔄</button>

  <div id="overlay">
    <div class="emoji">🤟</div>
    <p>Apunta la cámara de tu celular a tus manos.<br/>
       Tu laptop las detecta con <strong>MediaPipe</strong> en tiempo real.</p>
    <button class="btn-start" id="btn-start">📷 Activar cámara</button>
    <label for="access-key">Clave de acceso del operador</label>
    <input id="access-key" type="password" autocomplete="off" maxlength="512"/>
    <p>No se guardan imágenes. Esta demo detecta manos; aún no reconoce señas.</p>
  </div>
</div>

<!-- PANEL INFERIOR -->
<div class="bottom">
  <div class="actions">
    <button id="btn-stop" type="button">Detener cámara</button>
    <button id="btn-clear" type="button">Limpiar texto</button>
    <label><input id="voice-enabled" type="checkbox"/> Leer texto confirmado</label>
  </div>
  <p id="preflight">Cámara: requiere permiso · Modelo: pendiente · Arduino: futuro opcional</p>
  <p id="voice-state">Voz desactivada</p>
  <p id="status" role="status" aria-live="polite">Preparado para iniciar</p>
  <section class="output" aria-label="Salida de traducción">
    <p>Candidato: <span id="candidate">—</span></p>
    <p>Glosas pendientes: <span id="pending-glosses">—</span></p>
    <p>Texto confirmado: <span id="confirmed-text">—</span></p>
    <p id="model-state">Reconocimiento pendiente: modelo no disponible</p>
  </section>
  <ol id="history" class="history" aria-label="Historial de texto confirmado"></ol>
  <!-- Stats -->
  <div class="stats-row">
    <div class="stat"><div class="stat-v" id="s-fps">—</div><div class="stat-l">FPS</div></div>
    <div class="stat"><div class="stat-v" id="s-lat">—</div><div class="stat-l">ms</div></div>
    <div class="stat"><div class="stat-v" id="s-hands">0</div><div class="stat-l">Manos</div></div>
    <div class="stat"><div class="stat-v" id="s-kp">0</div><div class="stat-l">Keypts</div></div>
  </div>

  <!-- Manos detectadas -->
  <div id="hands-row"><div class="no-hands">Activa la cámara para empezar</div></div>

  <!-- Vector keypoints -->
  <canvas id="kp-canvas" height="46"></canvas>
</div>

<canvas id="cap-canvas" style="display:none"></canvas>
</main>

<script src="/static/app.js" defer></script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# RUTAS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template_string(_HTML, model_ready=_predictor is not None)


@app.route("/process_frame", methods=["POST"])
def process_frame():
    raise ApiError(410, "LEGACY_REMOVED", "Use la interfaz actual con sesión autorizada.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def process_v1_jpeg(image_bytes):
    if _detector is None:
        raise ApiError(503, "DETECTOR_UNAVAILABLE", "El detector no está disponible.")
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ApiError(400, "INVALID_FRAME", "No se pudo decodificar el JPEG.")
    if image.shape[1] > 1280 or image.shape[0] > 720:
        raise ApiError(413, "IMAGE_TOO_LARGE", "La imagen excede el límite permitido.")
    with _detector_lock:
        results = _detector.process(image)
        annotated = _detector.draw(image.copy(), results)
        hands = [{"side": item["label"], "confidence": item["confidence"] / 100}
                 for item in _detector.meta(results)]
        keypoints = _detector.keypoints(results)
    encoded, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 78])
    if not encoded:
        raise RuntimeError("JPEG encoding failed")
    return {"frame": "data:image/jpeg;base64," + base64.b64encode(buffer).decode(),
            "hands": hands, "keypoints": keypoints}


_predictor, _model_version = None, None
_sessions = SessionManager(os.environ.get("LSP_ACCESS_KEY"),
    os.environ.get("LSP_ALLOWED_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000").split(","),
    session_factory=lambda: TranslationPipeline(InferenceEngine(_predictor, _model_version)))


def enrich_features(frame, result, session):
    return session["pipeline"].push(frame.frame_id, frame.captured_at_ms, result["keypoints"])


register_frame_api(app, process_v1_jpeg, _sessions.acquire, enrich_features)
register_sessions(app, _sessions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--model-dir", type=Path, default=None, help="Artefactos locales de procedencia aprobada")
    args = parser.parse_args()
    if args.model_dir:
        _predictor, _model_version = load_predictor(args.model_dir)
    if not _sessions.access_key or len(_sessions.access_key) < 32:
        parser.error("Configure LSP_ACCESS_KEY con al menos 32 caracteres; no se imprime su valor.")
    if "LSP_ALLOWED_ORIGINS" not in os.environ:
        _sessions.allowed_origins = frozenset({f"http://127.0.0.1:{args.port}", f"http://localhost:{args.port}"})
        if args.host not in ("127.0.0.1", "localhost", "::1"):
            parser.error("Para acceso remoto configure LSP_ALLOWED_ORIGINS explícitamente.")

    print("[INFO] Cargando MediaPipe Hands...")
    _detector = HandDetector()
    print("[OK]   MediaPipe listo.")
    print("=" * 50)
    print("  INTERPRETE LSP  -  Servidor de procesamiento")
    print("=" * 50)
    print(f"  URL local : http://localhost:{args.port}")
    print(f"  Red local : http://192.168.x.x:{args.port}")
    print(f"  Modo      : solo procesa frames de clientes")
    print(f"              (NO usa camara del laptop)")
    print("  Ctrl+C para detener")
    print("=" * 50)

    # Session IDs are capability tokens: the development access log must not log URLs.
    logging.getLogger("werkzeug").disabled = True
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
