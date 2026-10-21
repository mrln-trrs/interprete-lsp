import re
import shutil
import unittest
from pathlib import Path
from config.actions import EXTENDED_ACTIONS
from src.logic.validator import GlossValidator, prolog_accepts, valid_prediction


class TestLogic(unittest.TestCase):
    def test_boundaries(self):
        self.assertFalse(valid_prediction(1, 0.8499, 10))
        self.assertTrue(valid_prediction(1, 0.85, 10))
        self.assertTrue(valid_prediction(1, 0.8501, 11))
        self.assertFalse(valid_prediction(1, 0.9, 9))
        self.assertFalse(valid_prediction(1, float("nan"), 10))
        self.assertFalse(valid_prediction(True, 0.9, 10))

    def test_prolog_vocabulary_matches_python(self):
        rules = Path("src/logic/lsp_rules.pl").read_text(encoding="utf-8")
        self.assertEqual(int(re.search(r"class_count\((\d+)\)", rules).group(1)), len(EXTENDED_ACTIONS))

    @unittest.skipUnless(shutil.which("swipl"), "SWI-Prolog no instalado")
    def test_prolog_parity(self):
        last = len(EXTENDED_ACTIONS) - 1
        for class_id in (-1, 0, 1, 8, 9, last, last + 1):
            for confidence in (0.8499, 0.85, 0.8501, 1.0, 1.0001):
                for stable in (9, 10, 11):
                    with self.subTest(class_id=class_id, confidence=confidence, stable=stable):
                        self.assertEqual(prolog_accepts(class_id, confidence, stable, timeout=5),
                                         valid_prediction(class_id, confidence, stable))

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
