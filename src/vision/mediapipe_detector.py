"""
src/vision/mediapipe_detector.py
Detector de manos basado en MediaPipe Hands para el intérprete de Lengua de Señas Peruana (LSP).
Extrae coordenadas 3D (x, y, z) de 21 puntos articulares por mano en un vector fijo de 126 dimensiones.
"""

import time
from typing import Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np

import config.settings as settings


class HandDetector:
    """Encapsula la detección de manos y extracción de puntos clave usando MediaPipe."""

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
    ):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process_frame(self, frame: np.ndarray):
        """Procesa una imagen BGR y retorna los resultados de detección de MediaPipe."""
        # MediaPipe requiere formato RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Optimización: marcar como no escribible mejora el rendimiento
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True
        return results

    def draw_landmarks(self, frame: np.ndarray, results) -> np.ndarray:
        """Dibuja los puntos y conexiones de las manos detectadas sobre el frame."""
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )
        return frame

    def extract_keypoints(self, results) -> np.ndarray:
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
        if hasattr(self, "hands") and self.hands:
            self.hands.close()

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

