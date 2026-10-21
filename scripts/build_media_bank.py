"""
scripts/build_media_bank.py
Extrae secuencias y bancos de prototipos desde C:\\proyectos\\media paso por paso:
  1. numbers  -> Números 1 al 20 (Imagen 16.45.56.jpeg + Video 16.45.37.mp4)
  2. alphabet -> Abecedario A-Z + Ñ (Imagen 15.10.56.jpeg + Video 15.10.57.mp4)
  3. months   -> Meses ENERO-DICIEMBRE:
                 - Variante completa léxica/bimanual (Video 16.52.36.mp4)
                 - Variante abreviada/conversacional inicializada con rotación (Imagen 16.53.00.jpeg)
"""
import argparse
import json
from pathlib import Path
import sys
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.media_bank import compute_window_descriptor
from src.vision.mediapipe_detector import HandDetector
from src.vision.normalization import normalize_keypoints_vector
from src.vision.temporal import resample_sequence

NUMBER_INTERVALS = [
    ("1", 500, 1750, "static"),
    ("2", 2750, 4300, "static"),
    ("3", 5700, 7400, "static"),
    ("4", 8600, 10400, "static"),
    ("5", 11600, 13300, "static"),
    ("6", 14100, 16100, "static"),
    ("7", 16900, 19100, "static"),
    ("8", 19900, 22100, "static"),
    ("9", 22900, 24700, "static"),
    ("10", 25700, 27500, "static"),
    ("11", 28500, 30400, "dynamic_transition"),
    ("12", 31100, 33800, "dynamic_transition"),
    ("13", 34600, 36700, "dynamic_transition"),
    ("14", 37300, 40000, "dynamic_transition"),
    ("15", 40700, 43100, "dynamic_transition"),
    ("16", 43900, 46400, "dynamic_transition"),
    ("17", 46900, 49400, "dynamic_transition"),
    ("18", 49900, 52400, "dynamic_transition"),
    ("19", 53100, 56100, "dynamic_transition"),
    ("20", 56700, 59600, "dynamic_transition"),
]

ALPHABET_INTERVALS = [
    ("A", 250, 1650, "static"),
    ("B", 1950, 2800, "static"),
    ("C", 3100, 4450, "static"),
    ("D", 5100, 6500, "static"),
    ("E", 7100, 9100, "static"),
    ("F", 10300, 12300, "static"),
    ("G", 13100, 14450, "static"),
    ("H", 14750, 15750, "static"),
    ("I", 16050, 17450, "static"),
    ("J", 17650, 19450, "dynamic_transition"),
    ("K", 20100, 22400, "dynamic_transition"),
    ("L", 23100, 24550, "static"),
    ("M", 25250, 26550, "static"),
    ("N", 27050, 28550, "static"),
    ("Ñ", 28850, 31150, "dynamic_transition"),
    ("O", 31850, 33450, "static"),
    ("P", 34100, 36400, "static"),
    ("Q", 37600, 40900, "dynamic_transition"),
    ("R", 42100, 44400, "static"),
    ("S", 45100, 46550, "static"),
    ("T", 47100, 49300, "static"),
    ("U", 49850, 51550, "static"),
    ("V", 51850, 52850, "static"),
    ("W", 53050, 54550, "static"),
    ("X", 55300, 58400, "dynamic_transition"),
    ("Y", 59100, 61400, "static"),
    ("Z", 62100, 64450, "dynamic_transition"),
]

MONTH_INTERVALS = [
    ("ENERO", 300, 2400, "dynamic_bimanual"),
    ("FEBRERO", 3400, 6600, "dynamic_bimanual"),
    ("MARZO", 7900, 10300, "dynamic_bimanual"),
    ("ABRIL", 11400, 14800, "dynamic_bimanual"),
    ("MAYO", 16200, 19000, "dynamic_bimanual"),
    ("JUNIO", 20000, 22400, "dynamic_bimanual"),
    ("JULIO", 23500, 28300, "dynamic_bimanual"),
    ("AGOSTO", 29400, 33200, "dynamic_bimanual"),
    ("SETIEMBRE", 34400, 38200, "dynamic_bimanual"),
    ("OCTUBRE", 39400, 43000, "dynamic_bimanual"),
    ("NOVIEMBRE", 44200, 47200, "dynamic_bimanual"),
    ("DICIEMBRE", 48200, 51000, "dynamic_bimanual"),
]

# Mapeo de la variante abreviada/conversacional de cada mes (según imagen 16.53.00.jpeg):
# Configuración manual base (letra inicial o forma de mano asociada) + giro/oscilación de muñeca
MONTH_ABBREVIATED_SHAPES = {
    "ENERO": "E",
    "FEBRERO": "F",
    "MARZO": "H",       # Dedos índice y medio horizontales hacia la sien/oreja con giro
    "ABRIL": "A",       # Puño con pulgar lateral girando cerca del oído
    "MAYO": "B",        # Palma abierta dedos juntos con giro
    "JUNIO": "I",       # Meñique arriba con rotación
    "JULIO": "Y",       # Pulgar, índice y meñique (corazón/meñique) con giro
    "AGOSTO": "A",      # Pulgar extendido en giro
    "SETIEMBRE": "S",   # Puño cerrado en rotación
    "OCTUBRE": "O",     # Mano en O con rotación
    "NOVIEMBRE": "U",   # Índice y medio juntos extendidos con rotación
    "DICIEMBRE": "D",   # Índice arriba y resto en O con rotación
}


def extract_video_clip(cap, detector, start_ms, end_ms):
    fps = cap.get(cv2.CAP_PROP_FPS)
    f0 = int(start_ms * fps / 1000)
    f1 = int(end_ms * fps / 1000)
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
    raw_vectors = []
    norm_vectors = []
    timestamps = []
    for idx in range(f0, f1):
        ok, frame = cap.read()
        if not ok:
            break
        res = detector.process_frame(frame)
        kp = detector.extract_keypoints(res)
        if np.any(kp != 0):
            t_ms = (idx - f0) * 1000.0 / fps
            raw_vectors.append(kp)
            norm_vectors.append(normalize_keypoints_vector(kp))
            timestamps.append(t_ms)
    return raw_vectors, norm_vectors, timestamps


def save_npy_sequence(out_dir, gloss, source_tag, norm_vectors, timestamps):
    if len(timestamps) < 2:
        return None
    # Seleccionar el sub-segmento continuo más largo sin huecos > 200 ms
    best_vecs, best_ts = [], []
    cur_vecs, cur_ts = [norm_vectors[0]], [timestamps[0]]
    for vec, t in zip(norm_vectors[1:], timestamps[1:]):
        if t - cur_ts[-1] <= 195.0:
            cur_vecs.append(vec)
            cur_ts.append(t)
        else:
            if len(cur_ts) > len(best_ts):
                best_vecs, best_ts = cur_vecs, cur_ts
            cur_vecs, cur_ts = [vec], [t]
    if len(cur_ts) > len(best_ts):
        best_vecs, best_ts = cur_vecs, cur_ts
    if len(best_ts) < 2:
        return None
    ts = np.asarray(best_ts, dtype=np.float64)
    ts = ts - ts[0]
    duration = ts[-1]
    if duration < 1000.0 or np.any(np.diff(ts) > 200.0):
        ts = np.linspace(0.0, max(1050.0, float(len(best_vecs) * 40)), len(best_vecs))
    seq, _ = resample_sequence(best_vecs, ts)
    target_dir = Path(out_dir) / gloss
    target_dir.mkdir(parents=True, exist_ok=True)
    npy_path = target_dir / f"seq_{source_tag}.npy"
    np.save(npy_path, seq, allow_pickle=False)
    return str(npy_path.relative_to(PROJECT_ROOT))


def build_numbers_bank(media_dir: Path, out_bank: Path, out_npy: Path):
    img_path = media_dir / "WhatsApp Image 2026-10-20 at 16.45.56.jpeg"
    vid_path = media_dir / "WhatsApp Video 2026-10-20 at 16.45.37.mp4"
    prototypes = []

    # 1. Extraer de la imagen de referencia (Números 1 al 10, manos reales)
    img = cv2.imread(str(img_path))
    h, w, _ = img.shape
    with HandDetector(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.3) as det:
        for r in range(2):
            for c in range(5):
                gloss = str(r * 5 + c + 1)
                y0, y1 = int(r * h / 2), int((r + 1) * h / 2)
                x0, x1 = int(c * w / 5), int((c + 1) * w / 5)
                crop = img[y0:y1, x0:x1]
                padded = cv2.copyMakeBorder(crop, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                res = det.process_frame(padded)
                kp = det.extract_keypoints(res)
                if np.any(kp != 0):
                    desc = compute_window_descriptor([kp] * 10)
                    if desc:
                        prototypes.append({
                            "gloss": gloss,
                            "category": "numbers",
                            "source": "image_16.45.56_grid",
                            "motion_kind": "static",
                            **desc,
                        })

    # 2. Extraer del video (Números 1 al 20)
    cap = cv2.VideoCapture(str(vid_path))
    with HandDetector(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.35, min_tracking_confidence=0.35) as det:
        for gloss, s_ms, e_ms, motion_kind in NUMBER_INTERVALS:
            raw_vecs, norm_vecs, ts = extract_video_clip(cap, det, s_ms, e_ms)
            # Usar el núcleo central del clip (15% a 85%) para evitar el puño de transición inicial/final
            n = len(raw_vecs)
            core = raw_vecs[max(0, int(n * 0.15)):max(2, int(n * 0.85))] if n >= 6 else raw_vecs
            desc = compute_window_descriptor(core)
            if desc:
                prototypes.append({
                    "gloss": gloss,
                    "category": "numbers",
                    "source": "video_16.45.37",
                    "motion_kind": motion_kind,
                    **desc,
                })
                save_npy_sequence(out_npy, gloss, f"media_num_{gloss}", norm_vecs, ts)
    cap.release()

    out_bank.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "numbers-media-bank-v1",
        "category": "numbers",
        "classes": [str(i) for i in range(1, 21)],
        "prototype_count": len(prototypes),
        "prototypes": prototypes,
    }
    out_bank.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_alphabet_bank(media_dir: Path, out_bank: Path, out_npy: Path):
    img_path = media_dir / "WhatsApp Image 2026-10-20 at 15.10.56.jpeg"
    vid_path = media_dir / "WhatsApp Video 2026-10-20 at 15.10.57.mp4"
    prototypes = []

    # 1. Extraer del video continuo (27 letras A-Z + Ñ)
    cap = cv2.VideoCapture(str(vid_path))
    with HandDetector(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.35, min_tracking_confidence=0.35) as det:
        for gloss, s_ms, e_ms, motion_kind in ALPHABET_INTERVALS:
            raw_vecs, norm_vecs, ts = extract_video_clip(cap, det, s_ms, e_ms)
            n = len(raw_vecs)
            core = raw_vecs[max(0, int(n * 0.15)):max(2, int(n * 0.85))] if n >= 6 else raw_vecs
            desc = compute_window_descriptor(core)
            if desc:
                prototypes.append({
                    "gloss": gloss,
                    "category": "alphabet",
                    "source": "video_15.10.57",
                    "motion_kind": motion_kind,
                    **desc,
                })
                safe_tag = "NN" if gloss == "Ñ" else gloss
                save_npy_sequence(out_npy, gloss, f"media_alpha_{safe_tag}", norm_vecs, ts)
    cap.release()

    # 2. Extraer recortes detectables de la lámina 15.10.56.jpeg como refuerzo estático
    img = cv2.imread(str(img_path))
    if img is not None:
        h, w, _ = img.shape
        # La cuadrícula de círculos está entre y=[17%, 86%], x=[7%, 93%], 6 filas x 5 columnas
        grid_letters = [
            ["A", "B", "C", "D", "E"],
            ["F", "G", "H", "I", "J"],
            ["K", "L", "M", "N", "Ñ"],
            ["O", "P", "Q", "R", "S"],
            ["T", "U", "V", "W", "X"],
            ["Y", "Z"],
        ]
        y_top, y_bot = int(h * 0.17), int(h * 0.865)
        x_left, x_right = int(w * 0.065), int(w * 0.935)
        row_h = (y_bot - y_top) / 6.0
        col_w = (x_right - x_left) / 5.0
        dynamic_letters = {"J", "K", "Ñ", "Q", "X", "Z"}
        with HandDetector(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.3) as det:
            for r, row in enumerate(grid_letters):
                for c, gloss in enumerate(row):
                    if gloss in dynamic_letters:
                        continue
                    cy0 = int(y_top + r * row_h)
                    cy1 = int(y_top + (r + 1) * row_h)
                    cx0 = int(x_left + c * col_w)
                    cx1 = int(x_left + (c + 1) * col_w)
                    crop = img[cy0:cy1, cx0:cx1]
                    padded = cv2.copyMakeBorder(crop, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                    res = det.process_frame(padded)
                    kp = det.extract_keypoints(res)
                    if np.any(kp != 0):
                        desc = compute_window_descriptor([kp] * 10)
                        if desc:
                            prototypes.append({
                                "gloss": gloss,
                                "category": "alphabet",
                                "source": "image_15.10.56_grid",
                                "motion_kind": "static",
                                **desc,
                            })

    out_bank.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "alphabet-media-bank-v1",
        "category": "alphabet",
        "classes": [item[0] for item in ALPHABET_INTERVALS],
        "prototype_count": len(prototypes),
        "prototypes": prototypes,
    }
    out_bank.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_months_bank(media_dir: Path, out_bank: Path, out_npy: Path, alphabet_bank_path: Path):
    vid_path = media_dir / "WhatsApp Video 2026-10-20 at 16.52.36.mp4"
    prototypes = []

    # 1. Variante léxica completa en LSP desde el video 16.52.36.mp4
    cap = cv2.VideoCapture(str(vid_path))
    with HandDetector(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.35, min_tracking_confidence=0.35) as det:
        for gloss, s_ms, e_ms, motion_kind in MONTH_INTERVALS:
            raw_vecs, norm_vecs, ts = extract_video_clip(cap, det, s_ms, e_ms)
            n = len(raw_vecs)
            core = raw_vecs[max(0, int(n * 0.12)):max(2, int(n * 0.88))] if n >= 6 else raw_vecs
            desc = compute_window_descriptor(core)
            if desc:
                prototypes.append({
                    "gloss": gloss,
                    "category": "months",
                    "variant": "complete_video",
                    "source": "video_16.52.36",
                    "motion_kind": motion_kind,
                    **desc,
                })
                save_npy_sequence(out_npy, gloss, f"media_month_{gloss}", norm_vecs, ts)
    cap.release()

    # 2. Variante abreviada/conversacional (Imagen 16.53.00.jpeg):
    # configuración de la inicial + rotación/oscilación de muñeca
    if alphabet_bank_path.is_file():
        alpha_data = json.loads(alphabet_bank_path.read_text(encoding="utf-8"))
        by_letter = {}
        for proto in alpha_data.get("prototypes", []):
            if proto.get("source") == "video_15.10.57" or proto["gloss"] not in by_letter:
                by_letter[proto["gloss"]] = proto
        for month_gloss, base_letter in MONTH_ABBREVIATED_SHAPES.items():
            base_proto = by_letter.get(base_letter)
            if base_proto:
                prototypes.append({
                    "gloss": month_gloss,
                    "category": "months",
                    "variant": f"abbreviated_rotated_{base_letter}",
                    "source": "image_16.53.00_abbreviated_rule",
                    "motion_kind": "rotated_initial",
                    "pose_mean": base_proto["pose_mean"],
                    "pose_start": base_proto["pose_start"],
                    "pose_end": base_proto["pose_end"],
                    "secondary_mean": [0.0] * len(base_proto["pose_mean"]),
                    "pose_change": 0.18,
                    "finger_jitter": 0.025,
                    "wrist_range_x": 0.30,
                    "wrist_range_y": 0.15,
                    "wrist_reversals": 2,
                    "bimanual_ratio": 0.0,
                })

    out_bank.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "months-media-bank-v1",
        "category": "months",
        "classes": [item[0] for item in MONTH_INTERVALS],
        "prototype_count": len(prototypes),
        "prototypes": prototypes,
    }
    out_bank.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Construir bancos de señas desde C:\\proyectos\\media")
    parser.add_argument("--media-dir", type=Path, default=Path(r"C:\proyectos\media"))
    parser.add_argument("--out-banks", type=Path, default=PROJECT_ROOT / "models" / "gestures")
    parser.add_argument("--out-npy", type=Path, default=PROJECT_ROOT / "data" / "keypoints_media")
    parser.add_argument("--step", choices=("numbers", "alphabet", "months", "all"), default="all")
    args = parser.parse_args()

    summary = {}
    if args.step in ("numbers", "all"):
        res = build_numbers_bank(args.media_dir, args.out_banks / "numbers_bank.json", args.out_npy)
        summary["numbers"] = {"classes": len(res["classes"]), "prototypes": res["prototype_count"]}
    if args.step in ("alphabet", "all"):
        res = build_alphabet_bank(args.media_dir, args.out_banks / "alphabet_bank.json", args.out_npy)
        summary["alphabet"] = {"classes": len(res["classes"]), "prototypes": res["prototype_count"]}
    if args.step in ("months", "all"):
        res = build_months_bank(
            args.media_dir,
            args.out_banks / "months_bank.json",
            args.out_npy,
            args.out_banks / "alphabet_bank.json",
        )
        summary["months"] = {"classes": len(res["classes"]), "prototypes": res["prototype_count"]}

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
