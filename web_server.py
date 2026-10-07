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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<title>LSP — Detección de Manos</title>
<style>
:root{
  --bg:#0a0d14; --card:#111827; --border:#1e2a3a;
  --accent:#00e5a0; --accent2:#3b82f6;
  --text:#e2e8f0; --muted:#64748b;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{
  font-family:'Inter',sans-serif;
  background:var(--bg); color:var(--text);
  display:flex; flex-direction:column;
}

/* ---- Header ---- */
header{
  flex-shrink:0;
  padding:12px 16px;
  display:flex; align-items:center; gap:10px;
  background:rgba(17,24,39,.9);
  backdrop-filter:blur(10px);
  border-bottom:1px solid var(--border);
  z-index:10;
}
.logo{
  width:32px; height:32px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  border-radius:8px;
  display:flex; align-items:center; justify-content:center;
  font-size:15px; flex-shrink:0;
}
header h1{font-size:.9rem; font-weight:700; line-height:1.2}
header p{font-size:.65rem; color:var(--muted)}
.pill{
  margin-left:auto;
  display:flex; align-items:center; gap:5px;
  background:rgba(0,229,160,.08);
  border:1px solid rgba(0,229,160,.25);
  border-radius:999px; padding:3px 10px;
  font-size:.68rem; color:var(--accent); font-weight:600;
  white-space:nowrap;
}
.dot{width:6px;height:6px;border-radius:50%;background:var(--accent);animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* ---- Video area (takes available height) ---- */
.video-section{
  position:relative;
  flex:1;
  background:#000;
  overflow:hidden;
  display:flex; align-items:center; justify-content:center;
}
#processed-img{
  width:100%; height:100%;
  object-fit:contain;
  display:block;
}

/* Start overlay */
#overlay{
  position:absolute; inset:0;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:14px;
  background:rgba(10,13,20,.93);
  backdrop-filter:blur(6px);
  padding:24px;
}
#overlay .emoji{font-size:3.5rem}
#overlay p{
  font-size:.88rem; color:var(--muted);
  text-align:center; line-height:1.6;
  max-width:280px;
}
.btn-start{
  display:inline-flex; align-items:center; gap:10px;
  background:linear-gradient(135deg,var(--accent),#00c27a);
  border:none; border-radius:14px;
  padding:14px 30px;
  font-size:1rem; font-weight:700; color:#050810;
  cursor:pointer; transition:transform .15s,opacity .2s;
}
.btn-start:active{transform:scale(.96)}

/* Flip button */
#btn-flip{
  position:absolute; bottom:12px; right:12px;
  width:42px; height:42px;
  background:rgba(17,24,39,.85);
  border:1px solid var(--border);
  border-radius:50%;
  display:none; align-items:center; justify-content:center;
  font-size:1.25rem; cursor:pointer;
}

/* Latency badge (top-right corner on video) */
#lat-badge{
  position:absolute; top:10px; right:10px;
  background:rgba(10,13,20,.78);
  border:1px solid var(--border);
  border-radius:6px; padding:3px 9px;
  font-size:.7rem; color:var(--muted);
  backdrop-filter:blur(4px);
  display:none;
}
#lat-badge span{color:var(--accent);font-weight:700}

/* ---- Bottom panel ---- */
.bottom{
  flex-shrink:0;
  background:var(--card);
  border-top:1px solid var(--border);
  padding:12px 14px;
  display:flex; flex-direction:column; gap:10px;
}

/* Stats row */
.stats-row{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:8px;
}
.stat{
  background:rgba(255,255,255,.03);
  border:1px solid var(--border);
  border-radius:10px;
  padding:8px 6px;
  text-align:center;
}
.stat-v{font-size:1.1rem;font-weight:900;color:var(--accent);line-height:1}
.stat-l{font-size:.58rem;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-top:3px}

/* Hands row */
#hands-row{display:flex;gap:8px;flex-wrap:wrap}
.hand-chip{
  display:flex; align-items:center; gap:7px;
  background:rgba(0,229,160,.06);
  border:1px solid var(--accent);
  border-radius:10px;
  padding:7px 12px;
  font-size:.8rem;
  animation:fadeIn .3s;
}
@keyframes fadeIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.hand-chip .icon{font-size:1.2rem}
.conf-mini{
  width:60px; height:3px;
  background:var(--border);
  border-radius:2px;
  margin-top:3px;
  overflow:hidden;
}
.conf-mini-fill{
  height:100%;
  background:linear-gradient(90deg,var(--accent2),var(--accent));
  border-radius:2px;
  transition:width .35s ease;
}
.no-hands{color:var(--muted);font-size:.8rem;padding:4px 0}

/* Keypoints mini bar */
#kp-canvas{
  width:100%;
  border-radius:6px;
  background:#060a10;
  border:1px solid var(--border);
}
</style>
</head>
<body>

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
<div class="video-section">
  <video id="local-video" playsinline autoplay muted style="display:none"></video>
  <img id="processed-img"
    src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
    alt=""/>

  <div id="lat-badge">Latencia: <span id="lat-val">—</span> ms</div>
  <button id="btn-flip" title="Cambiar cámara">🔄</button>

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
  <button id="btn-stop" type="button">Detener cámara</button>
  <p id="status" role="status" aria-live="polite">Preparado para iniciar</p>
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

<script>
// ── Config ────────────────────────────────────────────────────────────────
const TARGET_FPS = 12;
const JPEG_Q    = 0.65;
const MAX_W     = 640;

// ── Refs ───────────────────────────────────────────────────────────────────
const video    = document.getElementById('local-video');
const procImg  = document.getElementById('processed-img');
const capCanvas= document.getElementById('cap-canvas');
const capCtx   = capCanvas.getContext('2d');
const kpCanvas = document.getElementById('kp-canvas');
const kpCtx    = kpCanvas.getContext('2d');
const overlay  = document.getElementById('overlay');
const btnStart = document.getElementById('btn-start');
const btnFlip  = document.getElementById('btn-flip');
const livePill = document.getElementById('live-pill');
const latBadge = document.getElementById('lat-badge');
const latVal   = document.getElementById('lat-val');
const sFps     = document.getElementById('s-fps');
const sLat     = document.getElementById('s-lat');
const sHands   = document.getElementById('s-hands');
const sKp      = document.getElementById('s-kp');
const handsRow = document.getElementById('hands-row');

// ── Estado ─────────────────────────────────────────────────────────────────
let stream      = null;
let facing      = 'user';
let sending     = false;
let lastSend    = 0;
let frameCount  = 0;
let fpsTs       = Date.now();
let displayFps  = 0;
let sessionId = null;
let sessionStart = 0;
let frameId = 0;
let generation = 0;
let starting = false;
let inFlight = null;
const statusText = document.getElementById('status');

async function stopCamera() {
  generation++;
  inFlight?.abort();
  stream?.getTracks().forEach(t => t.stop());
  stream = null;
  video.srcObject = null;
  const closingSession = sessionId;
  sessionId = null;
  overlay.style.display = 'flex';
  livePill.style.display = 'none';
  btnFlip.style.display = 'none';
  statusText.textContent = 'Cámara detenida';
  if (closingSession) {
    try { await fetch('/api/v1/sessions/' + closingSession, {
      method:'DELETE', headers:{Authorization:'Bearer ' + closingSession},
      signal:AbortSignal.timeout(3000), keepalive:true
    }); } catch(e) { statusText.textContent = 'Cámara detenida; la sesión expira automáticamente'; }
  }
}
document.getElementById('btn-stop').addEventListener('click', stopCamera);
window.addEventListener('pagehide', stopCamera);

// ── Activar cámara ──────────────────────────────────────────────────────────
async function startCamera() {
  if (starting || stream) return;
  starting = true;
  const openingGeneration = ++generation;
  try {
    if (!sessionId) {
      const keyInput = document.getElementById('access-key');
      const accessKey = keyInput.value;
      keyInput.value = '';
      const response = await fetch('/api/v1/sessions', {
        method:'POST', headers:{'Content-Type':'application/json', Authorization:'Bearer ' + accessKey},
        body:'{}', signal:AbortSignal.timeout(3000)
      });
      if (!response.ok) throw new Error('No se pudo autorizar la sesión. Revisa la clave o disponibilidad.');
      sessionId = (await response.json()).data.session_id;
      sessionStart = performance.now(); frameId = 0;
      if (openingGeneration !== generation) { await stopCamera(); return; }
    }
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: facing, width:{ideal:1280}, height:{ideal:720} },
      audio: false
    });
    if (openingGeneration !== generation) { stream.getTracks().forEach(t => t.stop()); stream = null; return; }
    video.srcObject = stream;
    await video.play();
    overlay.style.display  = 'none';
    btnFlip.style.display  = 'flex';
    livePill.style.display = 'flex';
    latBadge.style.display = 'block';
    statusText.textContent = 'Detectando manos';
    requestAnimationFrame(() => loop(openingGeneration));
  } catch(e) {
    await stopCamera();
    statusText.textContent = e.message;
  } finally {
    starting = false;
  }
}
btnStart.addEventListener('click', startCamera);

btnFlip.addEventListener('click', async () => {
  stream?.getTracks().forEach(t => t.stop());
  stream = null; generation++; inFlight?.abort();
  facing = facing === 'user' ? 'environment' : 'user';
  await startCamera();
});

// ── Loop de captura ─────────────────────────────────────────────────────────
function loop(loopGeneration) {
  if (!stream || loopGeneration !== generation) return;
  requestAnimationFrame(() => loop(loopGeneration));
  const now = Date.now();
  if ((now - lastSend) < 1000 / TARGET_FPS) return;
  if (sending || video.readyState < 2) return;
  lastSend = now;
  send();
  frameCount++;
  if (now - fpsTs >= 1000) { displayFps = frameCount; frameCount = 0; fpsTs = now; }
}

async function send() {
  sending = true;
  const t0 = Date.now();
  const vw = video.videoWidth  || 640;
  const vh = video.videoHeight || 480;
  const sc = Math.min(1, MAX_W / vw);
  capCanvas.width  = Math.round(vw * sc);
  capCanvas.height = Math.round(vh * sc);
  capCtx.drawImage(video, 0, 0, capCanvas.width, capCanvas.height);
  const dataUrl = capCanvas.toDataURL('image/jpeg', JPEG_Q);
  const sendingGeneration = generation;
  inFlight = new AbortController();
  const timeout = setTimeout(() => inFlight?.abort(), 3000);
  try {
    const r = await fetch('/api/v1/process-frame', {
      method:'POST',
      headers:{'Content-Type':'application/json', Authorization:'Bearer ' + sessionId},
      body: JSON.stringify({ frame: dataUrl, session_id:sessionId,
        frame_id:frameId++, captured_at_ms:performance.now() - sessionStart }),
      signal:inFlight.signal
    });
    if (!r.ok) {
      statusText.textContent = 'Procesamiento no disponible; detén y vuelve a iniciar';
      if ([401,403,503].includes(r.status)) await stopCamera();
      return;
    }
    const d = (await r.json()).data;
    if (sendingGeneration !== generation) return;
    d.manos = d.hands.map(h => ({label:h.side,
      label_es:h.side === 'Left' ? 'Izquierda' : 'Derecha', confidence:Math.round(h.confidence * 100)}));
    const lat = Date.now() - t0;
    if (d.frame) procImg.src = d.frame;
    sFps.textContent   = displayFps;
    sLat.textContent   = lat;
    sHands.textContent = (d.manos||[]).length;
    const kp = d.keypoints||[];
    sKp.textContent    = kp.filter(v=>v!==0).length;
    latVal.textContent = lat;
    renderHands(d.manos||[]);
    renderKP(kp);
  } catch(e){ if (sendingGeneration === generation) statusText.textContent = 'Conexión interrumpida'; }
  finally{ clearTimeout(timeout); inFlight = null; sending=false; }
}

// ── Render manos ──────────────────────────────────────────────────────────
function renderHands(manos) {
  handsRow.innerHTML = '';
  if (!manos.length) {
    handsRow.innerHTML = '<div class="no-hands">✋ No se detectan manos</div>';
    return;
  }
  manos.forEach(m => {
    const icon = m.label === 'Left' ? '🤚' : '✋';
    const d = document.createElement('div');
    d.className = 'hand-chip';
    d.innerHTML = `
      <span class="icon">${icon}</span>
      <div>
        <div style="font-weight:600;font-size:.82rem">Mano ${m.label_es}</div>
        <div style="font-size:.7rem;color:var(--muted)">${m.confidence}%</div>
        <div class="conf-mini"><div class="conf-mini-fill" style="width:${m.confidence}%"></div></div>
      </div>`;
    handsRow.appendChild(d);
  });
}

// ── Render keypoints ─────────────────────────────────────────────────────────
function renderKP(kp) {
  const w = kpCanvas.offsetWidth || 300;
  kpCanvas.width  = w;
  kpCanvas.height = 46;
  kpCtx.clearRect(0, 0, w, 46);
  if (!kp.length) return;
  const bw  = Math.max(1, (w - kp.length) / kp.length);
  const mid = 23;
  const g   = kpCtx.createLinearGradient(0,0,w,0);
  g.addColorStop(0,   'rgba(59,130,246,.85)');
  g.addColorStop(.5,  'rgba(0,229,160,.85)');
  g.addColorStop(1,   'rgba(59,130,246,.85)');
  kpCtx.fillStyle = g;
  kp.forEach((v,i) => {
    const x = i*(bw+1);
    const h = Math.abs(v)*20+1;
    kpCtx.fillRect(x, mid-h/2, bw, h);
  });
}
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# RUTAS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template_string(_HTML)


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


_sessions = SessionManager(os.environ.get("LSP_ACCESS_KEY"),
    os.environ.get("LSP_ALLOWED_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000").split(","))
register_frame_api(app, process_v1_jpeg, _sessions.acquire)
register_sessions(app, _sessions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
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
