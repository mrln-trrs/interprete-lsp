"""
src/training/train.py
Pipeline de entrenamiento, validación y evaluación de métricas (F1, matriz de confusión).
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import numpy as np
from config.actions import ACTIONS
from src.dataset.dataset_loader import load_dataset, split_dataset
from src.dataset.record_samples import atomic_json
from src.training.model_builder import build_lstm_model
from src.vision.temporal import FEATURE_SCHEMA, NORMALIZATION_VERSION, MIRROR_CONVENTION


def classification_metrics(actual, predicted, num_classes=len(ACTIONS)):
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    if actual.ndim != 1 or actual.shape != predicted.shape or len(actual) == 0:
        raise ValueError("Etiquetas vacías o incompatibles")
    if actual.dtype.kind not in "iu" or predicted.dtype.kind not in "iu" or np.any(actual < 0) or np.any(predicted < 0) or np.any(actual >= num_classes) or np.any(predicted >= num_classes):
        raise ValueError("Etiquetas fuera de rango")
    confusion = np.zeros((num_classes, num_classes), dtype=np.int64)
    np.add.at(confusion, (actual, predicted), 1)
    correct = confusion.diagonal().astype(float)
    support = confusion.sum(axis=1)
    precision = np.divide(correct, confusion.sum(axis=0), out=np.zeros(num_classes), where=confusion.sum(axis=0) > 0)
    recall = np.divide(correct, support, out=np.zeros(num_classes), where=support > 0)
    f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros(num_classes), where=precision + recall > 0)
    return {"accuracy": float(np.mean(actual == predicted)), "macro_f1": float(f1.mean()),
            "precision": precision.tolist(), "recall": recall.tolist(), "f1": f1.tolist(),
            "support": support.tolist(), "confusion_matrix": confusion.tolist()}


def prepare_training(root, allow_unreviewed=False):
    dataset = load_dataset(root, allow_unreviewed)
    splits = split_dataset(dataset)
    counts = np.bincount(dataset.labels, minlength=len(ACTIONS))
    return dataset, splits, {"status": "DRY_RUN", "samples": len(dataset.labels),
                            "class_counts": dict(zip(ACTIONS, counts.tolist())),
                            "splits": {name: len(indices) for name, indices in splits.items()},
                            "manifest_sha256": dataset.manifest_sha256,
                            "minimum_30_per_class": bool(np.all(counts >= 30)),
                            "unreviewed_allowed": allow_unreviewed, "metrics": None}


def run_training(dataset, splits, output_dir, epochs=100, evaluate_test=False, allow_unreviewed=False):
    if np.any(np.bincount(dataset.labels, minlength=len(ACTIONS)) < 30):
        raise ValueError("El corpus no alcanza 30 muestras por clase; no se entrena")
    if not 1 <= epochs <= 100:
        raise ValueError("Épocas fuera de rango")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    test_gate = output_dir / "test-opened.json"
    if evaluate_test and test_gate.exists():
        raise ValueError("Test ya abierto en este directorio; preservar evaluación y usar corpus nuevo")
    models, histories = {}, {}
    try:
        import tensorflow as tf
        callbacks = tf.keras.callbacks
    except ImportError as error:
        raise RuntimeError("ENV-03 bloqueado: Keras no está disponible") from error
    train, validation = splits["train"], splits["validation"]
    for recurrent in ("lstm", "gru"):
        tf.keras.utils.set_random_seed(42)
        model = build_lstm_model(recurrent=recurrent)
        history = model.fit(dataset.features[train], dataset.labels[train],
                            validation_data=(dataset.features[validation], dataset.labels[validation]),
                            epochs=epochs, batch_size=16,
                            callbacks=[callbacks.EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)], verbose=2)
        models[recurrent], histories[recurrent] = model, history.history
    selected = min(histories, key=lambda name: min(histories[name]["val_loss"]))
    model = models[selected]
    artifact = output_dir / "lsp_model.keras"
    model.save(artifact)
    loaded = tf.keras.models.load_model(artifact, compile=False)
    fixture = dataset.features[validation[:2]]
    np.testing.assert_allclose(model(fixture, training=False).numpy(), loaded(fixture, training=False).numpy(), atol=1e-5, rtol=1e-5)
    metadata = {"schema_version": FEATURE_SCHEMA, "normalization_version": NORMALIZATION_VERSION,
                "mirror_convention": MIRROR_CONVENTION, "class_order": ACTIONS, "seed": 42,
                "python": platform.python_version(), "tensorflow": tf.__version__,
                "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "manifest_sha256": dataset.manifest_sha256, "model_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "selected": selected, "histories": histories, "test_metrics": None,
                "exploratory": allow_unreviewed, "release_approved": False}
    if evaluate_test:
        atomic_json(test_gate, {"manifest_sha256": dataset.manifest_sha256, "status": "opened"})
        test = splits["test"]
        probabilities = model(dataset.features[test], training=False).numpy()
        metadata["test_metrics"] = classification_metrics(dataset.labels[test], np.argmax(probabilities, axis=1))
        majority = int(np.bincount(dataset.labels[train], minlength=len(ACTIONS)).argmax())
        metadata["majority_baseline"] = classification_metrics(dataset.labels[test], np.full(len(test), majority))
    atomic_json(output_dir / "label_encoder.json", {"classes": ACTIONS, "schema_version": FEATURE_SCHEMA})
    atomic_json(output_dir / "metadata.json", metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Baseline LSP reproducible, test reservado")
    parser.add_argument("--root", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--output", type=Path, default=Path("models/trained"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--allow-unreviewed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--evaluate-test", action="store_true")
    args = parser.parse_args()
    try:
        dataset, splits, plan = prepare_training(args.root, args.allow_unreviewed)
        if args.dry_run:
            print(json.dumps(plan, indent=2))
            return 0
        run_training(dataset, splits, args.output, args.epochs, args.evaluate_test, args.allow_unreviewed)
        print("Artefactos guardados; el release requiere auditoría y revisión lingüística")
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
