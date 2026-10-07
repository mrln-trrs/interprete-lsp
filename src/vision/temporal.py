"""Fixed-duration windows shared by recording and inference."""
import numpy as np

FEATURE_SCHEMA = "hands-126-v1"
NORMALIZATION_VERSION = "wrist-palm-v1"
MIRROR_CONVENTION = "mediapipe-selfie-input"
WINDOW_MS = 1000.0
MAX_GAP_MS = 200.0


def resample_sequence(vectors, timestamps_ms):
    features = np.asarray(vectors, dtype=np.float64)
    timestamps = np.asarray(timestamps_ms, dtype=np.float64)
    if features.ndim != 2 or features.shape[1] != 126 or len(features) < 2:
        raise ValueError("Se requiere (N,126), N >= 2")
    if timestamps.shape != (len(features),) or not np.isfinite(timestamps).all() or not np.isfinite(features).all():
        raise ValueError("Datos temporales no válidos")
    gaps = np.diff(timestamps)
    if timestamps[0] < 0 or np.any(gaps <= 0):
        raise ValueError("Timestamps no monotónicos")
    if np.any(gaps > MAX_GAP_MS):
        raise ValueError("Hueco temporal mayor de 200 ms")
    end = timestamps[-1]
    start = end - WINDOW_MS
    if timestamps[0] > start + 1e-6:
        raise ValueError("Partial: cobertura temporal insuficiente")
    grid = np.linspace(start, end, 30)
    sequence = np.column_stack([np.interp(grid, timestamps, features[:, col]) for col in range(126)]).astype(np.float32)
    if not np.isfinite(sequence).all():
        raise ValueError("Remuestreo no finito")
    return sequence, grid
