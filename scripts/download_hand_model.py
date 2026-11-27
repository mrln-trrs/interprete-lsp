"""Descarga y verifica el modelo MediaPipe HandLandmarker (models/mediapipe/hand_landmarker.task, no versionado)."""
import argparse
from pathlib import Path

from src.vision.mediapipe_detector import HAND_MODEL_SHA256, ensure_hand_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Ruta de destino (por defecto models/mediapipe/hand_landmarker.task)")
    args = parser.parse_args()
    path = ensure_hand_model(args.output)
    print(f"[OK] {path} (sha256 {HAND_MODEL_SHA256})")


if __name__ == "__main__":
    main()
