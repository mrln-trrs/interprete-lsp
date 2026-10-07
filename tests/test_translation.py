import unittest
import numpy as np
from src.nlp.translator import translate_glosses, TranslationBuffer
from src.inference.engine import InferenceEngine
from src.inference.pipeline import TranslationPipeline


class TestTranslation(unittest.TestCase):
    def test_templates_and_unknown_sequence(self):
        self.assertEqual(translate_glosses(["YO", "QUERER", "AGUA"])["text"], "Yo quiero agua.")
        self.assertIsNone(translate_glosses(["YO", "HOLA"])["text"])
        self.assertIsNone(translate_glosses(["REPOSO"])["text"])
        with self.assertRaises(ValueError):
            translate_glosses(["UNKNOWN"])

    def test_buffer_deadline_and_limit(self):
        buffer = TranslationBuffer()
        buffer.append("HOLA", 0)
        self.assertFalse(buffer.due(9999))
        self.assertTrue(buffer.due(10000))
        self.assertEqual(buffer.flush()["text"], "Hola.")
        self.assertEqual(buffer.glosses, [])

    def test_fixture_pipeline_dispatches_only_after_stable_rest(self):
        current_class = [1]
        def predictor(sequence):
            probabilities = np.full(9, 0.01)
            probabilities[current_class[0]] = 0.92
            return probabilities
        pipeline = TranslationPipeline(InferenceEngine(predictor, "fixture-only"))
        for index in range(25):
            result = pipeline.push(index, index * 100, np.zeros(126))
        self.assertEqual(result["pending_glosses"], ["HOLA"])
        self.assertEqual(result["confirmed_text"], "")
        current_class[0] = 0
        for index in range(25, 35):
            result = pipeline.push(index, index * 100, np.zeros(126))
        self.assertEqual(result["confirmed_text"], "Hola.")
        self.assertEqual(result["pending_glosses"], [])
