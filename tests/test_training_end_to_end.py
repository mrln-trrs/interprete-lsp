import json
import os
from pathlib import Path
import tempfile
import unittest
import numpy as np
from config.actions import ACTIONS
from src.dataset.dataset_loader import load_dataset, split_dataset
from src.dataset.record_samples import save_sample
from src.inference.engine import InferenceEngine, load_predictor
from src.training.train import run_training


def class_vector(class_id, rng):
    """Mano derecha ya normalizada (muñeca en 0, nudillo medio a distancia 1); la punta del medio codifica la clase."""
    hand = np.zeros((21, 3))
    hand[9] = (0.0, 1.0, 0.0)
    angle = 2 * np.pi * class_id / len(ACTIONS)
    hand[12] = (1.5 * np.cos(angle), 1.5 * np.sin(angle), 0.0)
    hand[1:] += rng.normal(0, 0.02, (20, 3))
    return np.concatenate([np.zeros(63), hand.ravel()])


@unittest.skipUnless(os.environ.get("LSP_NATIVE_ML_TESTS") == "1", "Native ML opt-in; local Windows policy blocks optree")
class TestTrainingEndToEnd(unittest.TestCase):
    """MOD-02 con corpus sintético: acredita el código (fit, guardado, carga e inferencia), no la precisión real."""

    def test_fit_save_load_and_infer(self):
        import tensorflow as tf
        rng = np.random.default_rng(7)
        timestamps = np.linspace(0, 1000, 31)
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as output:
            # 10 participantes × 3 muestras = 30 por clase; split 6/2/2 cubre todas las clases.
            for participant in range(10):
                for class_id, gloss in enumerate(ACTIONS):
                    for _ in range(3):
                        frames = [class_vector(class_id, rng) for _ in timestamps]
                        save_sample(data_dir, gloss, frames, timestamps, f"p{participant}", "s", "fixture-permission", source="synthetic-test")
            dataset = load_dataset(data_dir, allow_unreviewed=True)
            metadata = run_training(dataset, split_dataset(dataset), output, epochs=40, evaluate_test=True, allow_unreviewed=True)

            self.assertFalse(metadata["release_approved"])
            self.assertIn(metadata["selected"], ("lstm", "gru"))
            self.assertGreaterEqual(metadata["test_metrics"]["accuracy"], 0.9)
            self.assertGreater(metadata["test_metrics"]["macro_f1"], metadata["majority_baseline"]["macro_f1"])
            self.assertEqual(json.loads((Path(output) / "label_encoder.json").read_text(encoding="utf-8"))["classes"], ACTIONS)
            with self.assertRaises(ValueError):  # El test reservado no se abre dos veces en el mismo directorio.
                run_training(dataset, split_dataset(dataset), output, epochs=1, evaluate_test=True, allow_unreviewed=True)

            predictor, version = load_predictor(output)
            self.assertEqual(version, metadata["model_sha256"])
            engine = InferenceEngine(predictor, version)
            for frame_id, timestamp in enumerate(np.arange(0, 1100, 33.0)):
                result = engine.push(frame_id, float(timestamp), class_vector(4, rng))
            self.assertEqual(result["state"], "Success")
            self.assertEqual(result["prediction"]["gloss"], ACTIONS[4])

            artifact = Path(output) / "lsp_model.keras"
            artifact.write_bytes(artifact.read_bytes() + b"x")
            with self.assertRaises(ValueError):  # Un artefacto alterado no se carga.
                load_predictor(output)
            tf.keras.backend.clear_session()


if __name__ == "__main__":
    unittest.main()
