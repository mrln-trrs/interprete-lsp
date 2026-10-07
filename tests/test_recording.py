import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from src.dataset.record_samples import save_sample


class TestRecording(unittest.TestCase):
    def test_atomic_sequence_and_unique_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            vectors = np.zeros((31, 126), np.float32)
            times = np.linspace(0, 1000, 31)
            entries = [save_sample(root, "HOLA", vectors, times, "p1", "s1", "consent:demo") for _ in range(2)]
            self.assertNotEqual(entries[0]["relative_path"], entries[1]["relative_path"])
            self.assertEqual(len(json.loads((root / "manifest.json").read_text())["samples"]), 2)
            saved = np.load(root / entries[0]["relative_path"], allow_pickle=False)
            self.assertEqual(saved.shape, (30, 126))
            self.assertEqual(saved.dtype, np.float32)
            self.assertFalse((root / ".capture.lock").exists())

    def test_bad_input_does_not_leave_a_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for gloss, times, permission in (("../HOLA", [0, 1000], "ok"), ("HOLA", [0, 1000], ""), ("HOLA", [0, 1000], "ok")):
                with self.assertRaises(ValueError):
                    save_sample(root, gloss, np.zeros((2, 126)), times, "p1", "s1", permission)
            self.assertEqual(list(root.rglob("*.npy")), [])

    def test_existing_lock_is_respected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".capture.lock").touch()
            with self.assertRaises(ValueError):
                save_sample(root, "HOLA", np.zeros((31, 126)), np.linspace(0, 1000, 31), "p", "s", "ok")
            self.assertTrue((root / ".capture.lock").exists())
