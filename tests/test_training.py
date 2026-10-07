import tempfile
import unittest
import numpy as np
from src.training.train import classification_metrics, prepare_training
import test_dataset


class TestTraining(unittest.TestCase):
    def test_metrics_known_confusion(self):
        result = classification_metrics([0, 0, 1, 1], [0, 1, 1, 1], 2)
        self.assertEqual(result["confusion_matrix"], [[1, 1], [0, 2]])
        self.assertEqual(result["accuracy"], 0.75)
        self.assertAlmostEqual(result["macro_f1"], (2 / 3 + 0.8) / 2)

    def test_metrics_invalid_input(self):
        for actual, predicted in (([], []), ([0], [9]), ([0.5], [0]), ([0, 1], [0])):
            with self.assertRaises(ValueError):
                classification_metrics(actual, predicted)

    def test_dry_run_never_reports_training_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            test_dataset.TestDataset().create(folder, True)
            _, _, plan = prepare_training(folder, True)
            self.assertIsNone(plan["metrics"])
            self.assertFalse(plan["minimum_30_per_class"])
            self.assertEqual(plan["status"], "DRY_RUN")
