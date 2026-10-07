import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from config.actions import ACTIONS
from src.dataset.record_samples import save_sample
from src.dataset.dataset_loader import load_dataset, split_dataset


class TestDataset(unittest.TestCase):
    def create(self, root, all_classes=False):
        for participant in range(5 if all_classes else 1):
            for gloss in ACTIONS if all_classes else ["HOLA"]:
                save_sample(root, gloss, np.zeros((31, 126)), np.linspace(0, 1000, 31), f"p{participant}", "s", "fixture-permission", source="synthetic-test")

    def test_group_split_and_no_leakage(self):
        with tempfile.TemporaryDirectory() as folder:
            self.create(folder, True)
            data = load_dataset(folder, allow_unreviewed=True)
            splits = split_dataset(data)
            self.assertEqual(data.features.shape, (45, 30, 126))
            groups = [set(data.groups[indices]) for indices in splits.values()]
            self.assertTrue(groups[0].isdisjoint(groups[1]))
            self.assertTrue(groups[0].isdisjoint(groups[2]))
            self.assertTrue(groups[1].isdisjoint(groups[2]))

    def test_review_and_checksum_gates(self):
        with tempfile.TemporaryDirectory() as folder:
            self.create(folder)
            with self.assertRaises(ValueError):
                load_dataset(folder)
            data = load_dataset(folder, True)
            path = Path(folder) / data.samples[0]["relative_path"]
            path.write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                load_dataset(folder, True)

    def test_path_escape_and_missing_groups(self):
        with tempfile.TemporaryDirectory() as folder:
            self.create(folder)
            data = load_dataset(folder, True)
            with self.assertRaises(ValueError):
                split_dataset(data)
            path = Path(folder) / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["samples"][0]["relative_path"] = "../outside.npy"
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                load_dataset(folder, True)
