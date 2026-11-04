"""Vocabulario configurable: corpus, entrenamiento, inferencia, validación y traducción con clases propias."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

from config.actions import ACTIONS
from src.dataset.dataset_loader import load_dataset, split_dataset
from src.dataset.record_samples import save_sample
from src.inference.engine import InferenceEngine
from src.inference.pipeline import TranslationPipeline
from src.logic.validator import GlossValidator
from src.nlp.translator import TranslationBuffer, translate_glosses
from src.training.model_builder import validate_configuration
from src.vocabulary import gloss_folder, load_vocabulary, validate_classes

CLASSES = ["PENSAR", "MUJER", "QUE?"]


class TestVocabulary(unittest.TestCase):
    def test_default_and_file(self):
        self.assertEqual(load_vocabulary(), ACTIONS)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "v.json"
            path.write_text(json.dumps({"classes": CLASSES}), encoding="utf-8")
            self.assertEqual(load_vocabulary(path), CLASSES)

    def test_invalid_vocabularies(self):
        for classes in (["UNA"], ["A", "A"], ["minúscula", "B"], ["A/B", "C"], "AB", None):
            with self.assertRaises(ValueError):
                validate_classes(classes)
        self.assertEqual(gloss_folder("QUE?"), "QUE_Q")

    def test_model_configuration_follows_vocabulary(self):
        validate_configuration(num_classes=3, classes=CLASSES)
        with self.assertRaises(ValueError):
            validate_configuration(num_classes=9, classes=CLASSES)


class TestCustomCorpus(unittest.TestCase):
    def test_loader_and_split_with_own_classes(self):
        with tempfile.TemporaryDirectory() as folder:
            for participant in range(5):
                for gloss in CLASSES:
                    save_sample(folder, gloss, np.zeros((31, 126)), np.linspace(0, 1000, 31), f"p{participant}", "s",
                                "CC0-1.0", source="fixture", allowed_glosses=CLASSES,
                                quality_status="reviewed", review_ref="anotación de prueba")
            self.assertTrue((Path(folder) / "QUE_Q").is_dir())
            data = load_dataset(folder, classes=CLASSES)  # Revisadas: no requiere allow_unreviewed
            self.assertEqual(data.classes, CLASSES)
            self.assertEqual(sorted(set(data.labels.tolist())), [0, 1, 2])
            self.assertEqual(set(split_dataset(data)), {"train", "validation", "test"})
            with self.assertRaises(ValueError):  # Con las 9 glosas base, nada de este corpus es válido
                load_dataset(folder)

    def test_reviewed_sample_requires_reference(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            save_sample(folder, "HOLA", np.zeros((31, 126)), np.linspace(0, 1000, 31), "p", "s", "ok",
                        quality_status="reviewed")


class TestCustomInference(unittest.TestCase):
    def predictor(self, winner):
        def predict(sequence):
            probabilities = np.full(len(CLASSES), 0.02)
            probabilities[winner] = 1 - 0.02 * (len(CLASSES) - 1)
            return probabilities
        predict.classes = CLASSES
        return predict

    def test_engine_names_glosses_with_model_classes(self):
        engine = InferenceEngine(self.predictor(2), "fixture")
        self.assertEqual(engine.classes, CLASSES)
        self.assertTrue(engine.immediate_translation)  # Sin REPOSO, cada glosa aceptada se muestra al momento
        for frame_id, timestamp in enumerate(np.arange(0, 1100, 33.0)):
            result = engine.push(frame_id, float(timestamp), np.zeros(126))
        self.assertEqual(result["prediction"]["gloss"], "QUE?")
        self.assertFalse(InferenceEngine().immediate_translation)

    def test_validator_uses_engine_vocabulary(self):
        validator = GlossValidator(CLASSES)
        decision = None
        for frame in range(10):
            decision = validator.update({"class_id": 0, "confidence": 0.9}, frame, frame * 100)
        self.assertEqual(decision["gloss"], "PENSAR")  # La clase 0 no es reposo si no se llama REPOSO

    def test_pipeline_shows_literal_text(self):
        pipeline = TranslationPipeline(InferenceEngine(self.predictor(1), "fixture"))
        for frame_id, timestamp in enumerate(np.arange(0, 2000, 33.0)):
            result = pipeline.push(frame_id, float(timestamp), np.zeros(126))
        self.assertEqual(result["confirmed_text"], "Mujer.")


class TestTranslationVocabulary(unittest.TestCase):
    def test_literal_reading_for_model_glosses(self):
        result = translate_glosses(["MUJER", "PENSAR"], CLASSES)
        self.assertEqual((result["text"], result["status"]), ("Mujer pensar.", "Partial"))
        self.assertEqual(translate_glosses(["QUE?"], CLASSES)["text"], "Que?")
        self.assertEqual(translate_glosses(["YO", "QUERER", "AGUA"], CLASSES)["text"], "Yo quiero agua.")
        with self.assertRaises(ValueError):
            translate_glosses(["MUJER"])  # Sin el vocabulario del modelo sigue siendo desconocida
        buffer = TranslationBuffer(CLASSES)
        buffer.append("CASA" if "CASA" in CLASSES else "MUJER", 0)
        self.assertEqual(buffer.flush()["text"], "Mujer.")


if __name__ == "__main__":
    unittest.main()
