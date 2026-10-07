"""Convert explicitly labeled local video intervals, preserving licensed provenance."""
import argparse
import json
from pathlib import Path
import numpy as np
from config.actions import ACTIONS
from src.dataset.record_samples import save_sample


def import_interval(video_path, start_ms, end_ms, gloss, participant_id, permission, root,
                    source, session_id, detector):
    import cv2
    from src.vision.normalization import normalize_keypoints_vector
    if gloss not in ACTIONS or not np.isfinite([start_ms, end_ms]).all() or start_ms < 0 or end_ms - start_ms < 1000:
        raise ValueError("La anotación requiere glosa permitida y al menos un segundo")
    cap = cv2.VideoCapture(str(video_path))
    try:
        if not cap.isOpened():
            raise ValueError("Video no disponible")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not np.isfinite(fps) or fps < 5:
            raise ValueError("Cadencia del video inválida")
        first_index = int(np.ceil(start_ms * fps / 1000))
        cap.set(cv2.CAP_PROP_POS_FRAMES, first_index)
        vectors, timestamps = [], []
        index = first_index
        while True:
            timestamp = index * 1000 / fps
            if timestamp > end_ms:
                break
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            results = detector.process_frame(frame)
            vectors.append(normalize_keypoints_vector(detector.extract_keypoints(results)))
            timestamps.append(timestamp - start_ms)
            index += 1
            # One interval yields one independent sample, not duplicate sliding windows.
            if len(timestamps) >= 2 and timestamps[-1] - timestamps[0] >= 1000:
                break
        return save_sample(root, gloss, vectors, timestamps, participant_id, session_id,
                           permission, source=source)
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description="Importar intervalos de corpus autorizado")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--videos-root", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("data/keypoints"))
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or index.get("license") != "CC0-1.0" or not isinstance(index.get("clips"), list):
        parser.error("Este importador inicial solo admite un índice CC0 verificado")
    from src.vision.mediapipe_detector import HandDetector
    root = args.videos_root.resolve()
    report = {"imported": 0, "excluded": 0}
    with HandDetector(static_image_mode=True) as detector:
        for clip in index["clips"]:
            try:
                path = (root / clip["video"]).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    raise ValueError("Ruta de video no autorizada")
                import_interval(path, clip["start_ms"], clip["end_ms"], clip["gloss"],
                                clip["participant_id"], index["permission_ref"], args.root,
                                index["source"], clip["session_id"], detector)
                report["imported"] += 1
            except (KeyError, ValueError, OSError):
                report["excluded"] += 1
    print(json.dumps(report))
    return 0 if report["imported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
