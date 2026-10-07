"""Report installed versions and exercise the actual native vision/ML stack."""
import importlib.metadata as metadata
import json
import platform
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    import cv2
    import mediapipe as mp
    import numpy as np
    import tensorflow as tf
    from src.vision.mediapipe_detector import HandDetector

    if sys.version_info[:2] != (3, 11):
        raise RuntimeError("The validated profile requires Python 3.11")
    with HandDetector(static_image_mode=True) as detector:
        result = detector.process_frame(np.zeros((480, 640, 3), np.uint8))
        vector = detector.extract_keypoints(result)
        assert vector.shape == (126,) and np.isfinite(vector).all()
    failures = []
    try:
        import ssl
        ssl.create_default_context()
    except ImportError:
        failures.append("SSL unavailable: OS application-control policy blocks _ssl")
    try:
        model = tf.keras.Sequential([tf.keras.layers.Input((30, 126)),
                                     tf.keras.layers.GRU(4),
                                     tf.keras.layers.Dense(9, activation="softmax")])
        output = model(np.zeros((1, 30, 126), np.float32), training=False).numpy()
        assert output.shape == (1, 9) and np.isfinite(output).all()
    except ImportError:
        failures.append("Keras unavailable: inspect optree native extension / OS policy")
    packages = sorted((dist.metadata["Name"], dist.version)
                      for dist in metadata.distributions())
    report = {"python": platform.python_version(),
                      "platform": platform.platform(),
                      "opencv": cv2.__version__, "mediapipe": mp.__version__,
                      "tensorflow": tf.__version__, "vision_smoke": "PASS",
                      "full_smoke": "BLOCKED" if failures else "PASS",
                      "failures": failures, "packages": dict(packages)}
    output_text = json.dumps(report, indent=2)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(output_text + "\n", encoding="utf-8")
    else:
        print(output_text)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
