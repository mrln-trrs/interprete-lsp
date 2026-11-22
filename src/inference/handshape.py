"""
src/inference/handshape.py
Demo de frases con gestos definidos a mano (reglas geométricas, sin red neuronal).

Cada gesto se reconoce por qué dedos están extendidos (índice, medio, anular, meñique),
medido como la distancia punta-muñeca frente a la distancia articulación-muñeca.
El saludo HOLA reutiliza la regla de la mano abierta que se agita (wave.py).
Las predicciones pasan por el mismo camino que un modelo: validador (0.85 y 10 cuadros),
buffer de glosas y plantillas de traducción. Es una demostración del flujo completo,
no un reconocimiento lingüístico de LSP.
"""
import json
from pathlib import Path
import numpy as np

from config.actions import ACTIONS
from src.inference.wave import WaveGreetingEngine
from src.vision.normalization import finite_array

FINGERS = ((8, 6), (12, 10), (16, 14), (20, 18))  # (punta, articulación) de índice, medio, anular y meñique


def finger_ratios(hand):
    """Distancia punta-muñeca / articulación-muñeca de cada dedo (2D). Extendido ≈ 1.3, doblado ≈ 0.8."""
    points = hand[:, :2]
    wrist = points[0]
    return [float(np.linalg.norm(points[tip] - wrist) / max(1e-6, np.linalg.norm(points[pip] - wrist)))
            for tip, pip in FINGERS]


def read_handshape(hand, cut=1.03, spread=0.18):
    """Devuelve el patrón de dedos ('1100' = índice y medio) y qué tan claro es (0 a 1)."""
    ratios = finger_ratios(hand)
    pattern = "".join("1" if ratio > cut else "0" for ratio in ratios)
    clarity = min(min(1.0, abs(ratio - cut) / spread) for ratio in ratios)
    return pattern, clarity


class HandshapeSentenceEngine:
    """Motor de reglas compatible con TranslationPipeline (mismo contrato que InferenceEngine)."""
    immediate_translation = False  # la frase se traduce al bajar la mano (REPOSO)

    def __init__(self, config_path=None):
        path = Path(config_path or Path(__file__).resolve().parents[2] / "models/gestures/handshapes_frases.json")
        self.config = json.loads(path.read_text(encoding="utf-8"))
        self.shapes = self.config["shapes"]
        unknown = [gloss for gloss in self.shapes.values() if gloss not in ACTIONS]
        if unknown:
            raise ValueError(f"Glosas fuera del vocabulario base: {unknown}")
        self.classes = list(ACTIONS)
        self.predictor = True  # marca de disponibilidad para la interfaz; no es un modelo entrenado
        self.model_version = self.config["version"]
        self.wave = WaveGreetingEngine()
        self.reset()

    def reset(self):
        self.wave.reset()
        self.last_frame_id = -1
        self.last_timestamp = -1

    def _prediction(self, gloss, confidence, frame_id):
        return {"class_id": self.classes.index(gloss), "gloss": gloss, "confidence": float(confidence),
                "confidence_kind": "rule_match", "model_version": self.model_version,
                "frame_id": frame_id, "status": "candidate"}

    def push(self, frame_id, timestamp_ms, raw_vector):
        if type(frame_id) is not int or frame_id <= self.last_frame_id or not np.isfinite(timestamp_ms) or timestamp_ms <= self.last_timestamp:
            raise ValueError("Frame/timestamp no monotónico")
        self.last_frame_id, self.last_timestamp = frame_id, timestamp_ms
        points = finite_array(raw_vector, (126,)).reshape(2, 21, 3)
        waved = self.wave.push(frame_id, timestamp_ms, raw_vector)["prediction"]["gloss"] == "HOLA"

        hands = [hand for hand in points
                 if np.any(hand) and np.linalg.norm(hand[9, :2] - hand[0, :2]) >= self.config["min_palm"]]
        if not hands:
            return {"state": "Partial", "reason": None, "prediction": self._prediction("REPOSO", 1.0, frame_id)}
        if waved:
            return {"state": "Success", "reason": None, "prediction": self._prediction("HOLA", 1.0, frame_id)}

        # Mano principal: la más cercana a la cámara (palma más grande en la imagen).
        hand = max(hands, key=lambda h: np.linalg.norm(h[9, :2] - h[0, :2]))
        pattern, clarity = read_handshape(hand, self.config["cut"], self.config["spread"])
        gloss = self.shapes.get(pattern)
        if gloss is None:
            return {"state": "Partial", "reason": "NO_MATCH", "prediction": None}
        # Confianza de la regla: 0.6 si algún dedo está a medio doblar, 1.0 si todos están claros.
        confidence = 0.6 + 0.4 * clarity
        return {"state": "Success", "reason": None, "prediction": self._prediction(gloss, confidence, frame_id)}
