import unittest
from src.logic.validator import GlossValidator, valid_prediction


class TestLogic(unittest.TestCase):
    def test_boundaries(self):
        self.assertFalse(valid_prediction(1, 0.8499, 10))
        self.assertTrue(valid_prediction(1, 0.85, 10))
        self.assertTrue(valid_prediction(1, 0.8501, 11))
        self.assertFalse(valid_prediction(1, 0.9, 9))
        self.assertFalse(valid_prediction(1, float("nan"), 10))
        self.assertFalse(valid_prediction(True, 0.9, 10))

    def test_stability_and_deduplication(self):
        validator = GlossValidator()
        prediction = {"class_id": 1, "confidence": 0.85}
        outputs = [validator.update(prediction, i, i * 100) for i in range(20)]
        self.assertEqual([item["gloss"] for item in outputs if item["gloss"]], ["HOLA"])
        self.assertEqual(outputs[8]["status"], "candidate")
        self.assertEqual(outputs[9]["status"], "accepted")
        self.assertEqual(validator.update(prediction, 19, 1900)["status"], "rejected")

    def test_gap_and_rest_rearm(self):
        validator = GlossValidator()
        hello = {"class_id": 1, "confidence": 0.9}
        for i in range(10):
            validator.update(hello, i, i * 100)
        for i in range(10, 20):
            result = validator.update({"class_id": 0, "confidence": 0.9}, i, i * 100)
        self.assertEqual(result["status"], "rest")
        for i in range(20, 30):
            result = validator.update(hello, i, i * 100)
        self.assertEqual(result["gloss"], "HOLA")
        self.assertEqual(validator.update({"class_id": 2, "confidence": 0.9}, 30, 3300)["stable_frames"], 1)
