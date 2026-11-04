"""
src/dataset/perusil.py
Corpus PeruSIL (PUCP-DGI156, licencia CC0 1.0) → muestras (30,126) del proyecto, en cuatro pasos:

    python -m src.dataset.perusil descargar --que anotaciones   # SRT.tar + tabla de participantes (~200 KB)
    python -m src.dataset.perusil plan                           # elige vocabulario y lista de clips
    python -m src.dataset.perusil descargar --que videos         # Videos.tar (~1.08 GB, reanudable)
    python -m src.dataset.perusil extraer                        # solo los 27 videos originales
    python -m src.dataset.perusil importar --aceptar-anotacion-fuente

Decisiones (ver docs/execution/DAT-05.md):
- Las señas anotadas duran 0.3–0.9 s; cada muestra es la ventana de 1 s centrada en la seña (incluye algo de
  contexto). No se estiran ni repiten clips.
- Se excluyen los tramos con movimiento de cámara que marca la tabla del corpus.
- Participante = columna «Participante» de la tabla: la partición por persona del entrenamiento no mezcla señantes.
- El vocabulario solo incluye glosas con suficientes ejemplos y presentes en train, validation y test con la
  misma partición (semilla 42) que usa src/dataset/dataset_loader.split_dataset.
"""
import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import tarfile
import unicodedata
import urllib.request

import numpy as np

from src.vocabulary import validate_classes

DATASET = "hdl:20.500.12534/OJYYYS"
LICENSE = "CC0-1.0"
SOURCE = "perusil-pucp-dgi156"
CONSENT_REF = f"{LICENSE} PUCP-DGI156 ({DATASET})"
REVIEW_REF = "Anotación SRT_SEGMENTED_SIGN del corpus PUCP-DGI156"
# Archivos publicados en https://datos.pucp.edu.pe (API Dataverse, versión 2 del dataset)
FILES = {
    "tabla": {"id": 14626, "name": "info_videos.tab", "md5": None, "size": 2073, "query": "?format=original"},
    "anotaciones": {"id": 14429, "name": "SRT.tar", "md5": "f31f59c5e84a1c74b2ebb2505b404129", "size": 196096},
    "videos": {"id": 14427, "name": "Videos.tar", "md5": "3bdc92bae940846a52a9c5374d12de21", "size": 1078811648},
}
URL = "https://datos.pucp.edu.pe/api/access/datafile/{id}{query}"
RAW = Path("data/raw_videos/perusil")
WINDOW_MS, MARGIN_MS = 1000.0, 60.0


def canonical(value):
    value = "".join(char for char in unicodedata.normalize("NFD", value.upper()) if not unicodedata.combining(char))
    return re.sub(r"\s+", "_", value.strip())


def to_ms(value):
    """«2:08» o «0:40» (minutos:segundos) de la tabla de participantes → milisegundos."""
    minutes, seconds = value.strip().split(":")
    return (int(minutes) * 60 + int(seconds)) * 1000


# ── Descarga ────────────────────────────────────────────────────────────────────────────────────

def download(key, folder=RAW):
    spec = FILES[key]
    folder.mkdir(parents=True, exist_ok=True)
    target, partial = folder / spec["name"], folder / (spec["name"] + ".part")
    if target.exists() and target.stat().st_size == spec["size"]:
        print(f"Ya descargado: {target}")
        return target
    offset = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(URL.format(id=spec["id"], query=spec.get("query", "")),
                                     headers={"Range": f"bytes={offset}-"} if offset else {})
    with urllib.request.urlopen(request, timeout=60) as response, open(partial, "ab" if offset else "wb") as output:
        if offset and response.status != 206:  # El servidor ignoró el rango: empezar de cero
            output.seek(0)
            output.truncate()
        done = output.tell()
        while chunk := response.read(1 << 20):
            output.write(chunk)
            done += len(chunk)
            if done % (50 << 20) < (1 << 20):
                print(f"  {spec['name']}: {done / spec['size']:.0%}")
    if partial.stat().st_size != spec["size"]:
        raise ValueError(f"{spec['name']}: tamaño {partial.stat().st_size} distinto del publicado {spec['size']}; reintentar")
    if spec["md5"]:
        digest = hashlib.md5()
        with open(partial, "rb") as source:
            while block := source.read(1 << 20):
                digest.update(block)
        if digest.hexdigest() != spec["md5"]:
            partial.unlink()
            raise ValueError(f"{spec['name']}: MD5 no coincide; archivo descartado")
    partial.replace(target)
    print(f"Descargado y verificado: {target}")
    return target


# ── Anotaciones y plan ──────────────────────────────────────────────────────────────────────────

def read_table(path):
    """Participante y tramos con movimiento de cámara de cada video."""
    videos = {}
    with open(path, encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            excluded = []
            for start, end in (("Inicio 1", "Final 1"), ("Inicio 2", "Final 2")):
                if row.get(start, "").strip():
                    finish = to_ms(row[end]) if row.get(end, "").strip() else float("inf")
                    excluded.append((to_ms(row[start]), finish))
            videos[row["Nombre Video"].strip()] = {"participant": int(row["Participante"]), "excluded_ms": excluded}
    return videos


def read_annotations(path):
    """Segmentos (video, glosa, inicio_ms, fin_ms) de SRT_SEGMENTED_SIGN, sin extraer el tar al disco."""
    segments = []
    with tarfile.open(path) as source:
        for member in source.getmembers():
            if not member.isfile() or "SRT_SEGMENTED_SIGN/" not in member.name or not member.name.endswith(".srt"):
                continue
            if member.size > 1024 * 1024:
                raise ValueError("Archivo de anotación demasiado grande")
            video = Path(member.name).stem
            text = source.extractfile(member).read().decode("utf-8-sig")
            for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
                lines = block.splitlines()
                index = next((i for i, line in enumerate(lines) if "-->" in line), None)
                if index is None:
                    continue
                times = re.findall(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", lines[index])
                gloss = canonical(" ".join(lines[index + 1:]))
                if len(times) == 2 and gloss:
                    start, end = [int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms) for h, m, s, ms in times]
                    if end > start:
                        segments.append({"video": video, "gloss": gloss, "start_ms": start, "end_ms": end})
    return segments


def participant_id(number):
    return f"perusil-p{number:02d}"


def simulated_split(participants, seed=42):
    """Misma regla que dataset_loader.split_dataset (60/20/20 por persona, semilla 42)."""
    groups = np.random.default_rng(seed).permutation(np.unique(participants))
    train = max(1, int(len(groups) * 0.6))
    validation = max(1, int(len(groups) * 0.2))
    return {"train": set(groups[:train]), "validation": set(groups[train:train + validation]),
            "test": set(groups[train + validation:])}


def build_plan(table, segments, min_samples=30, min_participants=10, max_classes=20, exclude=()):
    usable, discarded = [], Counter()
    for segment in segments:
        info = table.get(segment["video"])
        center = (segment["start_ms"] + segment["end_ms"]) / 2
        window = (center - WINDOW_MS / 2 - MARGIN_MS, center + WINDOW_MS / 2)
        if info is None:
            discarded["video sin participante"] += 1
        elif window[0] < 0:
            discarded["ventana antes del inicio del video"] += 1
        elif any(window[0] < end and start < window[1] for start, end in info["excluded_ms"]):
            discarded["tramo con movimiento de cámara"] += 1
        else:
            usable.append({**segment, "participant_id": participant_id(info["participant"])})
    by_gloss = defaultdict(list)
    for clip in usable:
        by_gloss[clip["gloss"]].append(clip)
    split = simulated_split([participant_id(info["participant"]) for info in table.values()])
    ranking = []
    for gloss, clips in by_gloss.items():
        people = {clip["participant_id"] for clip in clips}
        covered = all(people & members for members in split.values())
        if len(clips) >= min_samples and len(people) >= min_participants and covered and gloss not in exclude:
            ranking.append((len(clips), gloss))
    classes = [gloss for _, gloss in sorted(ranking, key=lambda item: (-item[0], item[1]))[:max_classes]]
    if len(classes) < 2:
        raise ValueError("Ninguna combinación de glosas cumple los mínimos; bajar --min-participants o --min-samples")
    validate_classes(classes)
    clips = sorted((clip for clip in usable if clip["gloss"] in classes),
                   key=lambda clip: (clip["video"], clip["start_ms"]))
    stats = {gloss: {"clips": len(by_gloss[gloss]),
                     "participants": len({clip["participant_id"] for clip in by_gloss[gloss]})} for gloss in classes}
    return {"source": SOURCE, "license": LICENSE, "dataset": DATASET, "permission_ref": CONSENT_REF,
            "criteria": {"min_samples": min_samples, "min_participants": min_participants, "max_classes": max_classes,
                         "window_ms": WINDOW_MS, "split_seed": 42, "excluded_glosses": sorted(exclude)},
            "classes": classes, "stats": stats, "discarded": dict(discarded),
            "split_participants": {name: sorted(members) for name, members in split.items()},
            "clips": clips}


# ── Videos ──────────────────────────────────────────────────────────────────────────────────────

def extract_videos(archive, table, destination):
    """Copia solo los videos originales listados en la tabla; nunca usa rutas del tar (sin path traversal)."""
    destination.mkdir(parents=True, exist_ok=True)
    wanted, best = set(table), {}
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            stem = Path(member.name).stem
            if member.isfile() and member.name.lower().endswith(".mp4") and stem in wanted:
                if stem not in best or member.size > best[stem].size:  # El original es el archivo más grande
                    best[stem] = member
        for stem, member in sorted(best.items()):
            target = destination / f"{stem}.mp4"
            if target.exists() and target.stat().st_size == member.size:
                continue
            with source.extractfile(member) as data, open(target, "wb") as output:
                while block := data.read(1 << 20):
                    output.write(block)
            print(f"  {target.name} ({member.size / 1e6:.0f} MB)")
    missing = wanted - set(best)
    if missing:
        print(f"Aviso: sin video original para {sorted(missing)}")
    return sorted(best)


def window_vectors(capture, detector, start_ms, end_ms):
    """Cuadros espejados (convención mediapipe-selfie-input) del intervalo, normalizados, con tiempos relativos."""
    import cv2
    from src.vision.normalization import normalize_keypoints_vector
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps < 5:
        raise ValueError("Cadencia del video inválida")
    first = int(np.floor(start_ms * fps / 1000))
    capture.set(cv2.CAP_PROP_POS_FRAMES, first)
    vectors, timestamps, with_hands, index = [], [], 0, first
    while index * 1000 / fps <= end_ms + 1000 / fps:
        ok, frame = capture.read()
        if not ok:
            break
        raw = detector.extract_keypoints(detector.process_frame(cv2.flip(frame, 1)))
        with_hands += bool(np.any(raw))
        vectors.append(normalize_keypoints_vector(raw))
        timestamps.append(index * 1000 / fps - start_ms)
        index += 1
    return vectors, timestamps, with_hands


def import_clips(plan, videos_dir, root, accept_source_annotation, min_hand_ratio=0.6):
    import cv2
    from src.dataset.record_samples import save_sample
    from src.vision.mediapipe_detector import HandDetector
    manifest = Path(root) / "manifest.json"
    done = set()
    if manifest.exists():
        for entry in json.loads(manifest.read_text(encoding="utf-8")).get("samples", []):
            origin = entry.get("origin") or {}
            done.add((origin.get("video"), origin.get("start_ms"), origin.get("gloss")))
    report = {"imported": Counter(), "excluded": Counter()}
    by_video = defaultdict(list)
    for clip in plan["clips"]:
        by_video[clip["video"]].append(clip)
    for video, clips in sorted(by_video.items()):
        path = Path(videos_dir) / f"{video}.mp4"
        if not path.is_file():
            report["excluded"]["video ausente"] += len(clips)
            continue
        capture = cv2.VideoCapture(str(path))
        try:
            # Un detector por video: el seguimiento de MediaPipe no debe arrastrarse entre videos.
            with HandDetector() as detector:
                for clip in clips:
                    key = (video, clip["start_ms"], clip["gloss"])
                    if key in done:
                        report["imported"][clip["gloss"]] += 1
                        continue
                    center = (clip["start_ms"] + clip["end_ms"]) / 2
                    start = center - WINDOW_MS / 2 - MARGIN_MS
                    try:
                        vectors, timestamps, with_hands = window_vectors(capture, detector, start, center + WINDOW_MS / 2)
                        if len(vectors) < 2 or with_hands / len(vectors) < min_hand_ratio:
                            raise ValueError("manos no detectadas en la ventana")
                        save_sample(root, clip["gloss"], vectors, timestamps, clip["participant_id"], video,
                                    plan["permission_ref"], source=SOURCE, allowed_glosses=plan["classes"],
                                    quality_status="reviewed" if accept_source_annotation else "unreviewed",
                                    review_ref=REVIEW_REF if accept_source_annotation else None,
                                    origin={"video": video, "start_ms": clip["start_ms"], "end_ms": clip["end_ms"],
                                            "gloss": clip["gloss"], "dataset": DATASET})
                        report["imported"][clip["gloss"]] += 1
                    except ValueError as error:
                        report["excluded"][str(error).split(":")[0]] += 1
        finally:
            capture.release()
        print(f"  {video}: {sum(report['imported'].values())} muestras acumuladas")
    return {"imported": dict(report["imported"]), "excluded": dict(report["excluded"]),
            "below_30": sorted(gloss for gloss in plan["classes"] if report["imported"][gloss] < 30)}


# ── Línea de comandos ───────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Corpus PeruSIL (CC0) → muestras del intérprete LSP")
    steps = parser.add_subparsers(dest="step", required=True)
    step = steps.add_parser("descargar", help="Baja archivos del repositorio de datos PUCP (verifica tamaño y MD5)")
    step.add_argument("--que", choices=("anotaciones", "videos"), required=True)
    step = steps.add_parser("plan", help="Elige vocabulario y lista de clips")
    step.add_argument("--min-samples", type=int, default=30)
    step.add_argument("--min-participants", type=int, default=10)
    step.add_argument("--max-classes", type=int, default=20)
    step.add_argument("--excluir", nargs="*", default=[], metavar="GLOSA",
                      help="Glosas a dejar fuera (p. ej. las que quedaron con menos de 30 muestras al importar)")
    step.add_argument("--vocabulary-out", type=Path, default=Path("config/vocabularies/perusil.json"))
    steps.add_parser("extraer", help="Saca de Videos.tar solo los videos originales")
    step = steps.add_parser("importar", help="Extrae keypoints y guarda muestras (30,126) con procedencia")
    step.add_argument("--root", type=Path, default=Path("data/keypoints_perusil"))
    step.add_argument("--aceptar-anotacion-fuente", action="store_true",
                      help="Marca las muestras como revisadas por la anotación experta del corpus")
    step.add_argument("--min-hand-ratio", type=float, default=0.6)
    args = parser.parse_args()
    plan_path = RAW / "plan.json"
    try:
        if args.step == "descargar":
            for key in (("tabla", "anotaciones") if args.que == "anotaciones" else ("videos",)):
                download(key)
        elif args.step == "plan":
            plan = build_plan(read_table(RAW / FILES["tabla"]["name"]), read_annotations(RAW / FILES["anotaciones"]["name"]),
                              args.min_samples, args.min_participants, args.max_classes, set(args.excluir))
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
            args.vocabulary_out.parent.mkdir(parents=True, exist_ok=True)
            args.vocabulary_out.write_text(json.dumps(
                {"name": "perusil", "source": SOURCE, "license": LICENSE, "dataset": DATASET,
                 "criteria": plan["criteria"], "classes": plan["classes"], "stats": plan["stats"]},
                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"classes": len(plan["classes"]), "clips": len(plan["clips"]), "stats": plan["stats"],
                              "discarded": plan["discarded"]}, ensure_ascii=False, indent=2))
        elif args.step == "extraer":
            names = extract_videos(RAW / FILES["videos"]["name"], read_table(RAW / FILES["tabla"]["name"]), RAW / "videos")
            print(f"{len(names)} videos listos en {RAW / 'videos'}")
        else:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            report = import_clips(plan, RAW / "videos", args.root, args.aceptar_anotacion_fuente, args.min_hand_ratio)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if report["below_30"]:
                print("Clases con menos de 30 muestras: rehacer el plan sin ellas (--max-classes o --min-samples)")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
