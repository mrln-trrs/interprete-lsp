from collections import deque
import hashlib
import json
from pathlib import Path
import numpy as np
from config.actions import ACTIONS
from src.vision.normalization import normalize_keypoints_vector
from src.vision.temporal import FEATURE_SCHEMA, NORMALIZATION_VERSION, MIRROR_CONVENTION, resample_sequence


def validate_artifacts(folder):
    folder = Path(folder)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    encoder = json.loads((folder / "label_encoder.json").read_text(encoding="utf-8"))
    expected = (FEATURE_SCHEMA, NORMALIZATION_VERSION, MIRROR_CONVENTION)
    actual = tuple(metadata.get(key) for key in ("schema_version", "normalization_version", "mirror_convention"))
    if actual != expected or metadata.get("class_order") != ACTIONS or encoder.get("classes") != ACTIONS or encoder.get("schema_version") != FEATURE_SCHEMA:
        raise ValueError("Modelo/encoder/esquema incompatibles")
    artifact = folder / "lsp_model.keras"
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != metadata.get("model_sha256"):
        raise ValueError("Checksum del modelo inválido")
    return artifact, metadata


def load_predictor(folder):
    artifact, metadata = validate_artifacts(folder)
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(artifact, compile=False)
    except ImportError as error:
        raise RuntimeError("ENV-03: runtime Keras no disponible") from error
    if tuple(model.input_shape[1:]) != (30, 126) or model.output_shape[-1] != len(ACTIONS):
        raise ValueError("Forma del modelo incompatible")
    return lambda sequence: model(sequence[None, ...], training=False).numpy()[0], metadata["model_sha256"]


class InferenceEngine:
    def __init__(self, predictor=None, model_version=None):
        self.predictor, self.model_version = predictor, model_version
        self.frames = deque(maxlen=65)
        self.last_frame_id = -1
        self.last_timestamp = -1

    def reset(self):
        self.frames.clear()
        self.last_frame_id = -1
        self.last_timestamp = -1

    def push(self, frame_id, timestamp_ms, raw_vector):
        if type(frame_id) is not int or frame_id <= self.last_frame_id or not np.isfinite(timestamp_ms) or timestamp_ms <= self.last_timestamp:
            raise ValueError("Frame/timestamp no monotónico")
        gap = self.last_timestamp >= 0 and timestamp_ms - self.last_timestamp > 200
        vector = normalize_keypoints_vector(raw_vector)
        if gap:
            self.frames.clear()
        self.last_frame_id, self.last_timestamp = frame_id, timestamp_ms
        self.frames.append((timestamp_ms, vector))
        while len(self.frames) > 2 and self.frames[1][0] < timestamp_ms - 1000:
            self.frames.popleft()
        if self.predictor is None:
            return {"state": "Partial", "reason": "MODEL_UNAVAILABLE", "prediction": None}
        try:
            sequence, _ = resample_sequence([frame[1] for frame in self.frames], [frame[0] for frame in self.frames])
        except ValueError:
            return {"state": "Partial", "reason": "TEMPORAL_GAP" if gap else "WINDOW_INCOMPLETE", "prediction": None}
        probabilities = np.asarray(self.predictor(sequence), dtype=float)
        if probabilities.shape != (len(ACTIONS),) or not np.isfinite(probabilities).all() or np.any(probabilities < 0) or np.any(probabilities > 1) or abs(probabilities.sum() - 1) > 1e-3:
            raise ValueError("Probabilidades de modelo inválidas")
        winning = int(probabilities.argmax())
        if np.count_nonzero(probabilities == probabilities[winning]) != 1:
            return {"state": "Partial", "reason": "AMBIGUOUS", "prediction": None}
        return {"state": "Success", "reason": None,
                "prediction": {"class_id": winning, "gloss": ACTIONS[winning], "confidence": float(probabilities[winning]),
                               "model_version": self.model_version, "frame_id": frame_id, "status": "candidate"}}
