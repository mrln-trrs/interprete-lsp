"""
src/vision/mediapipe_detector.py
Detector de manos basado en MediaPipe Tasks (HandLandmarker) para el intérprete de Lengua de Señas Peruana (LSP).
Extrae coordenadas 3D (x, y, z) de 21 puntos articulares por mano en un vector fijo de 126 dimensiones.

MediaPipe 0.10.30+ retiró la API heredada ``mp.solutions``. Este módulo usa la Tasks API y entrega los
resultados con la misma forma que la API heredada (``multi_hand_landmarks`` / ``multi_handedness``), de modo
que los consumidores existentes no cambian. El modelo ``hand_landmarker.task`` no se versiona: se descarga
en tiempo de ejecución (o con ``python -m scripts.download_hand_model``) y se verifica su SHA-256.
"""

import hashlib
import os
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import cv2
import mediapipe as mp
import numpy as np

# Garantizar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config.settings as settings

# Modelo oficial de MediaPipe (float16, versión 1). Se fija la versión y su hash para que la descarga sea reproducible.
HAND_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
HAND_MODEL_SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
DEFAULT_HAND_MODEL_PATH = PROJECT_ROOT / "models" / "mediapipe" / "hand_landmarker.task"

# 21 puntos de la mano: mismas conexiones que la API heredada (HAND_CONNECTIONS).
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_hand_model(path: Optional[Path] = None) -> Path:
    """Devuelve la ruta del modelo HandLandmarker; lo descarga y verifica si no existe.

    Ruta: argumento, variable ``LSP_HAND_MODEL_PATH`` o ``models/mediapipe/hand_landmarker.task``.
    Una ruta indicada por variable de entorno se usa tal cual (sin descargar ni verificar hash).
    """
    env_path = os.environ.get("LSP_HAND_MODEL_PATH")
    if path is None and env_path:
        custom = Path(env_path)
        if not custom.is_file():
            raise FileNotFoundError(f"LSP_HAND_MODEL_PATH no existe: {custom}")
        return custom
    target = Path(path) if path is not None else DEFAULT_HAND_MODEL_PATH
    if target.is_file() and _sha256(target) == HAND_MODEL_SHA256:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".hand_landmarker-", suffix=".part", dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with urllib.request.urlopen(HAND_MODEL_URL, timeout=60) as response, open(tmp, "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        actual = _sha256(tmp)
        if actual != HAND_MODEL_SHA256:
            raise RuntimeError(f"hand_landmarker.task con SHA-256 inesperado: {actual}")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return target


# Estructuras compatibles con la salida de la API heredada mp.solutions.hands.
@dataclass
class Landmark:
    x: float
    y: float
    z: float


@dataclass
class HandLandmarks:
    landmark: List[Landmark] = field(default_factory=list)


@dataclass
class Category:
    label: str
    score: float
    index: int = 0


@dataclass
class Handedness:
    classification: List[Category] = field(default_factory=list)


@dataclass
class HandResults:
    """Resultado con la forma de la API heredada: ``None`` en ambos campos si no hay manos."""

    multi_hand_landmarks: Optional[List[HandLandmarks]] = None
    multi_handedness: Optional[List[Handedness]] = None


def to_legacy_results(result) -> HandResults:
    """Convierte un ``HandLandmarkerResult`` de la Tasks API a la forma heredada."""
    if result is None or not result.hand_landmarks:
        return HandResults()
    hands, handedness = [], []
    for landmarks, categories in zip(result.hand_landmarks, result.handedness):
        hands.append(HandLandmarks([Landmark(float(p.x), float(p.y), float(p.z)) for p in landmarks]))
        top = categories[0]
        handedness.append(Handedness([Category(top.category_name, float(top.score), int(top.index or 0))]))
    return HandResults(hands, handedness)


def draw_hand_landmarks(frame: np.ndarray, results: HandResults) -> np.ndarray:
    """Dibuja los puntos y conexiones de las manos detectadas con OpenCV (sustituye a drawing_utils)."""
    if not results.multi_hand_landmarks:
        return frame
    h, w = frame.shape[:2]
    for hand in results.multi_hand_landmarks:
        pts = [(int(p.x * w), int(p.y * h)) for p in hand.landmark]
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (224, 224, 224), 2, cv2.LINE_AA)
        for i, pt in enumerate(pts):
            color = (48, 48, 255) if i in (0, 1, 5, 9, 13, 17) else (0, 204, 0)
            cv2.circle(frame, pt, 4, color, -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 4, (255, 255, 255), 1, cv2.LINE_AA)
    return frame


class HandDetector:
    """Encapsula la detección de manos y extracción de puntos clave usando MediaPipe HandLandmarker."""

    NUM_HAND_LANDMARKS = 21
    COORDINATES_PER_LANDMARK = 3  # (x, y, z)
    HAND_FEATURE_DIM = NUM_HAND_LANDMARKS * COORDINATES_PER_LANDMARK  # 63
    TOTAL_FEATURE_DIM = HAND_FEATURE_DIM * 2  # 126 (Mano Izquierda + Mano Derecha)

    def __init__(
        self,
        min_detection_confidence: float = settings.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence: float = settings.MIN_TRACKING_CONFIDENCE,
        max_num_hands: int = 2,
        static_image_mode: bool = False,
        model_path: Optional[Path] = None,
    ):
        vision = mp.tasks.vision
        self.static_image_mode = static_image_mode
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(ensure_hand_model(model_path))),
            running_mode=vision.RunningMode.IMAGE if static_image_mode else vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.hands = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def _next_timestamp_ms(self) -> int:
        # El modo VIDEO exige marcas de tiempo estrictamente crecientes.
        now = int(time.monotonic() * 1000)
        self._last_timestamp_ms = max(now, self._last_timestamp_ms + 1)
        return self._last_timestamp_ms

    def process_frame(self, frame: np.ndarray) -> HandResults:
        """Procesa una imagen BGR y retorna los resultados con la forma de la API heredada."""
        # MediaPipe requiere formato RGB contiguo
        rgb_frame = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        if self.static_image_mode:
            result = self.hands.detect(image)
        else:
            result = self.hands.detect_for_video(image, self._next_timestamp_ms())
        return to_legacy_results(result)

    def draw_landmarks(self, frame: np.ndarray, results: HandResults) -> np.ndarray:
        """Dibuja los puntos y conexiones de las manos detectadas sobre el frame."""
        return draw_hand_landmarks(frame, results)

    def extract_keypoints(self, results: HandResults) -> np.ndarray:
        """
        Extrae un vector unidimensional determinista de 126 valores:
        - Mano Izquierda: 63 valores (21 puntos * 3 coords). Si no se detecta, se rellena con 0.
        - Mano Derecha:   63 valores (21 puntos * 3 coords). Si no se detecta, se rellena con 0.
        """
        left_hand = np.zeros(self.HAND_FEATURE_DIM, dtype=np.float32)
        right_hand = np.zeros(self.HAND_FEATURE_DIM, dtype=np.float32)

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                label = handedness.classification[0].label  # "Left" o "Right"
                points = np.array(
                    [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                    dtype=np.float32,
                ).flatten()

                if label == "Left":
                    left_hand = points
                elif label == "Right":
                    right_hand = points

        return np.concatenate([left_hand, right_hand])

    def close(self):
        """Libera los recursos nativos de MediaPipe."""
        if getattr(self, "hands", None) is not None:
            self.hands.close()
            self.hands = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def run_live_camera(camera_index: int = 0):
    """Ejecuta la captura de cámara en tiempo real con dibujo de articulaciones."""
    print("Iniciando cámara web... (Presiona 'q' en la ventana para salir)")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Error: No se pudo abrir la cámara con índice {camera_index}.")
        print("Verifica que tu cámara esté conectada y que no esté siendo usada por otra aplicación.")
        return

    # Ajustar resolución si está soportada
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    prev_time = time.time()
    fps = 0.0

    with HandDetector() as detector:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error: No se pudo leer el frame de la cámara.")
                break

            # Modo espejo para interacción intuitiva
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Procesar detección
            results = detector.process_frame(frame)

            # Dibujar articulaciones de las manos
            detector.draw_landmarks(frame, results)

            # Calcular FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-6)
            prev_time = curr_time

            # Identificar manos detectadas
            detected_labels = []
            if results.multi_handedness:
                for classification in results.multi_handedness:
                    label = classification.classification[0].label
                    # Traducir etiqueta
                    label_es = "Izquierda" if label == "Left" else "Derecha"
                    confidence = classification.classification[0].score * 100
                    detected_labels.append(f"{label_es} ({confidence:.0f}%)")

            hands_text = ", ".join(detected_labels) if detected_labels else "Ninguna"

            # Overlay visual superior
            cv2.rectangle(frame, (10, 10), (450, 95), (20, 20, 20), -1)
            cv2.rectangle(frame, (10, 10), (450, 95), (0, 200, 100), 2)
            cv2.putText(
                frame,
                f"LSP - Detector MediaPipe | FPS: {fps:.1f}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"Manos: {hands_text}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255) if detected_labels else (120, 120, 120),
                2,
            )
            cv2.putText(
                frame,
                "Presiona 'q' para salir",
                (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 180, 180),
                1,
            )

            cv2.imshow("Interprete LSP - Deteccion de Manos (MediaPipe)", frame)

            # Salir con la tecla 'q' o ESC (27)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break

    cap.release()
    cv2.destroyAllWindows()
    print("Cámara cerrada correctamente.")


if __name__ == "__main__":
    run_live_camera()

