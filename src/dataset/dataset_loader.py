"""
src/dataset/dataset_loader.py
Carga de matrices .npy y generación de conjuntos de entrenamiento y prueba.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import numpy as np
from config.actions import ACTIONS
from src.vision.temporal import FEATURE_SCHEMA, NORMALIZATION_VERSION, MIRROR_CONVENTION


@dataclass
class Dataset:
    features: np.ndarray
    labels: np.ndarray
    groups: np.ndarray
    samples: list
    excluded: list
    manifest_sha256: str


def load_dataset(root="data/keypoints", allow_unreviewed=False):
    root = Path(root).resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Empty: falta manifest.json; no hay corpus entrenable")
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("samples"), list):
        raise ValueError("Manifiesto inválido")
    features, labels, groups, entries, excluded = [], [], [], [], []
    seen_ids, seen_paths = set(), set()
    for index, entry in enumerate(manifest["samples"]):
        try:
            if not isinstance(entry, dict):
                raise ValueError("Registro inválido")
            sample_id = entry["sample_id"]
            relative = entry["relative_path"]
            if not isinstance(sample_id, str) or not sample_id or sample_id in seen_ids or relative in seen_paths:
                raise ValueError("ID o ruta repetida")
            seen_ids.add(sample_id)
            seen_paths.add(relative)
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or Path(relative).is_absolute() or path.suffix != ".npy":
                raise ValueError("Ruta no autorizada")
            if entry["gloss"] not in ACTIONS or path.parent.name != entry["gloss"]:
                raise ValueError("Etiqueta/ruta incompatible")
            if (entry["schema_version"], entry["normalization_version"], entry["mirror_convention"]) != (FEATURE_SCHEMA, NORMALIZATION_VERSION, MIRROR_CONVENTION):
                raise ValueError("Esquema o lateralidad incompatibles")
            if any(not isinstance(entry.get(field), str) or not entry[field].strip() for field in ("participant_id", "session_id", "consent_ref", "source")):
                raise ValueError("Falta procedencia/grupo/permiso")
            if not allow_unreviewed and entry.get("quality_status") != "reviewed":
                raise ValueError("Muestra pendiente de revisión")
            if not path.is_file() or path.stat().st_size > 1024 * 1024:
                raise ValueError("Archivo ausente o excesivo")
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["checksum_sha256"]:
                raise ValueError("Checksum inválido")
            sequence = np.load(path, allow_pickle=False)
            if sequence.shape != (30, 126) or sequence.dtype != np.float32 or not np.isfinite(sequence).all():
                raise ValueError("Matriz inválida")
            timestamps = np.asarray(entry["timestamps_ms"], dtype=float)
            if timestamps.shape != (30,) or not np.isfinite(timestamps).all() or np.any(np.diff(timestamps) <= 0):
                raise ValueError("Timestamps inválidos")
            if abs(timestamps[-1] - timestamps[0] - 1000) > 1e-3 or float(entry["max_source_gap_ms"]) > 200:
                raise ValueError("Cobertura/gaps incompatibles")
            features.append(sequence)
            labels.append(ACTIONS.index(entry["gloss"]))
            groups.append(entry["participant_id"])
            entries.append(entry)
        except (KeyError, TypeError, ValueError, OSError) as error:
            excluded.append({"index": index, "reason": str(error)})
    if not features:
        raise ValueError(f"Empty: ninguna muestra válida; excluidas {len(excluded)}")
    return Dataset(np.stack(features), np.asarray(labels, dtype=np.int64), np.asarray(groups), entries,
                   excluded, hashlib.sha256(raw).hexdigest())


def split_dataset(dataset, seed=42):
    groups = np.unique(dataset.groups)
    if len(groups) < 5:
        raise ValueError("Se requieren al menos cinco participantes/grupos independientes")
    groups = np.random.default_rng(seed).permutation(groups)
    train_count = max(1, int(len(groups) * 0.6))
    validation_count = max(1, int(len(groups) * 0.2))
    partitions = (groups[:train_count], groups[train_count:train_count + validation_count], groups[train_count + validation_count:])
    result = {}
    for name, selected_groups in zip(("train", "validation", "test"), partitions):
        indices = np.flatnonzero(np.isin(dataset.groups, selected_groups))
        if set(dataset.labels[indices].tolist()) != set(range(len(ACTIONS))):
            raise ValueError(f"Cobertura insuficiente de clases en {name}; recopilar más datos")
        result[name] = indices
    return result


def main():
    parser = argparse.ArgumentParser(description="Validar corpus LSP y particiones por persona")
    parser.add_argument("--root", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--allow-unreviewed", action="store_true", help="Solo prototipo, no release")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.root, args.allow_unreviewed)
        splits = split_dataset(dataset)
        print(json.dumps({"shape": list(dataset.features.shape), "excluded": len(dataset.excluded),
                          "manifest_sha256": dataset.manifest_sha256,
                          "splits": {name: len(indices) for name, indices in splits.items()}}, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
