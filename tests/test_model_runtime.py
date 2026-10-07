import os
from pathlib import Path
import tempfile
import unittest
import numpy as np
from src.training.model_builder import build_lstm_model


@unittest.skipUnless(os.environ.get("LSP_NATIVE_ML_TESTS") == "1", "Native ML opt-in; local Windows policy blocks optree")
class TestNativeModel(unittest.TestCase):
    def test_baselines_compile_and_round_trip(self):
        import tensorflow as tf
        for recurrent in ("lstm", "gru"):
            with self.subTest(recurrent=recurrent), tempfile.TemporaryDirectory() as directory:
                model = build_lstm_model(recurrent=recurrent)
                fixture = np.zeros((2, 30, 126), dtype=np.float32)
                prediction = model(fixture, training=False).numpy()
                self.assertEqual(prediction.shape, (2, 9))
                np.testing.assert_allclose(prediction.sum(axis=1), np.ones(2), atol=1e-5)
                path = Path(directory) / "fixture.keras"
                model.save(path)
                loaded = tf.keras.models.load_model(path, compile=False)
                np.testing.assert_allclose(prediction, loaded(fixture, training=False).numpy(), atol=1e-5)
                tf.keras.backend.clear_session()
