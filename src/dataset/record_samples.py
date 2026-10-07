"""
src/dataset/record_samples.py
Script interactivo para captura y grabación de muestras de señas.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid

import numpy as np
from config.actions import ACTIONS
from src.vision.temporal import FEATURE_SCHEMA, NORMALIZATION_VERSION, MIRROR_CONVENTION, resample_sequence


@contextmanager
def recording_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".capture.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError("Otra grabación está activa; no se modifica el manifiesto") from None
    try:
        os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def atomic_json(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            json.dump(value, output, ensure_ascii=False, allow_nan=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def save_sample(root, gloss, vectors, timestamps_ms, participant_id, session_id, consent_ref,
                source="local-consented", mirror_convention=MIRROR_CONVENTION):
    if gloss not in ACTIONS:
        raise ValueError("Glosa no permitida")
    identifiers = (participant_id, session_id, consent_ref, source)
    if any(not isinstance(value, str) or not value.strip() or len(value) > 256 for value in identifiers):
        raise ValueError("Se requieren referencias de participante, sesión, permiso y origen")
    sequence, grid = resample_sequence(vectors, timestamps_ms)
    root = Path(root).resolve()
    with recording_lock(root):
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"version": 1, "samples": []}
        if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("samples"), list):
            raise ValueError("Manifiesto inválido")
        sample_id = uuid.uuid4().hex
        relative_path = f"{gloss}/seq_{sample_id}.npy"
        destination = (root / relative_path).resolve()
        if not destination.is_relative_to(root):
            raise ValueError("Ruta fuera del dataset")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        committed = False
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
                temporary = Path(output.name)
                np.save(output, sequence, allow_pickle=False)
                output.flush()
                os.fsync(output.fileno())
            checksum = hashlib.sha256(temporary.read_bytes()).hexdigest()
            os.replace(temporary, destination)
            timestamps = np.asarray(timestamps_ms, dtype=float)
            entry = {"sample_id": sample_id, "relative_path": relative_path, "gloss": gloss,
                     "participant_id": participant_id, "session_id": session_id, "consent_ref": consent_ref,
                     "source": source, "schema_version": FEATURE_SCHEMA, "normalization_version": NORMALIZATION_VERSION,
                     "mirror_convention": mirror_convention, "timestamps_ms": grid.tolist(), "duration_ms": 1000,
                     "capture_fps": (len(timestamps) - 1) * 1000 / (timestamps[-1] - timestamps[0]),
                     "max_source_gap_ms": float(np.diff(timestamps).max()), "shape": [30, 126], "dtype": "float32",
                     "checksum_sha256": checksum, "quality_status": "unreviewed", "split": None}
            manifest["samples"].append(entry)
            atomic_json(manifest_path, manifest)
            committed = True
            return entry
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
            if not committed:
                destination.unlink(missing_ok=True)


def capture_sequence(cap, detector, gloss):
    import cv2
    from src.vision.normalization import normalize_keypoints_vector
    vectors, timestamps = [], []
    start = time.perf_counter()
    countdown_end = start + 2
    while True:
        ok, frame = cap.read()
        if not ok:
            raise ValueError("Error: no se pudo leer la cámara")
        frame = cv2.flip(frame, 1)
        now = time.perf_counter()
        if now >= countdown_end:
            results = detector.process_frame(frame)
            vectors.append(normalize_keypoints_vector(detector.extract_keypoints(results)))
            timestamps.append((now - countdown_end) * 1000)
            detector.draw_landmarks(frame, results)
            state = "Loading: capturando"
        else:
            state = f"Loading: preparar {max(1, int(countdown_end - now) + 1)}"
        cv2.putText(frame, f"{gloss} | {state} | q/Esc cancela", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("LSP - Captura", frame)
        if cv2.waitKey(1) & 255 in (27, ord("q")):
            return None
        if len(timestamps) >= 2 and timestamps[-1] - timestamps[0] >= 1000:
            return vectors, timestamps


def main():
    parser = argparse.ArgumentParser(description="Captura consentida de muestras LSP")
    parser.add_argument("--gloss", choices=ACTIONS, required=True)
    parser.add_argument("--participant", required=True, help="Seudónimo, nunca nombre real")
    parser.add_argument("--consent-ref", required=True)
    parser.add_argument("--session", default=None)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--root", type=Path, default=Path("data/keypoints"))
    args = parser.parse_args()
    if not 1 <= args.samples <= 100:
        parser.error("samples debe estar entre 1 y 100")
    import cv2
    from src.vision.mediapipe_detector import HandDetector
    cap = cv2.VideoCapture(args.camera)
    try:
        if not cap.isOpened():
            raise ValueError("Error: cámara no disponible")
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        session = args.session or uuid.uuid4().hex
        with HandDetector() as detector:
            for _ in range(args.samples):
                captured = capture_sequence(cap, detector, args.gloss)
                if captured is None:
                    print("Idle: cancelado; no se guardó una muestra parcial")
                    return 0
                save_sample(args.root, args.gloss, *captured, args.participant, session, args.consent_ref)
                print("Success: muestra guardada, pendiente de revisión lingüística")
    except ValueError as error:
        print(str(error))
        return 1
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
