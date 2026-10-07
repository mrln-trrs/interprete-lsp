import unittest
import numpy as np
from src.inference.engine import InferenceEngine


class TestInference(unittest.TestCase):
    def predictor(self, sequence):
        self.assertEqual(sequence.shape, (30, 126))
        return np.array([0.01, 0.92] + [0.01] * 7)

    def test_window_gap_and_reset(self):
        engine = InferenceEngine(self.predictor, "fixture-not-a-model")
        for index in range(11):
            result = engine.push(index, index * 100, np.zeros(126))
        self.assertEqual(result["prediction"]["gloss"], "HOLA")
        self.assertEqual(result["prediction"]["status"], "candidate")
        self.assertIsNone(engine.push(11, 1300, np.zeros(126))["prediction"])
        with self.assertRaises(ValueError):
            engine.push(11, 1300, np.zeros(126))
        engine.reset()
        self.assertIsNone(engine.push(0, 0, np.zeros(126))["prediction"])

    def test_model_absence_is_explicit(self):
        result = InferenceEngine().push(0, 0, np.zeros(126))
        self.assertEqual(result["reason"], "MODEL_UNAVAILABLE")
        self.assertIsNone(result["prediction"])

    def test_invalid_model_output_is_rejected(self):
        engine = InferenceEngine(lambda sequence: np.full(9, np.nan))
        for index in range(10):
            engine.push(index, index * 100, np.zeros(126))
        with self.assertRaises(ValueError):
            engine.push(10, 1000, np.zeros(126))
