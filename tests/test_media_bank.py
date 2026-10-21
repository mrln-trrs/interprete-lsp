import json
from pathlib import Path
import unittest
import numpy as np

from config.actions import ALPHABET_ACTIONS, MONTH_ACTIONS, NUMBER_ACTIONS
from src.inference.media_bank import (
    MediaSignBankEngine,
    canonical_hand_pose,
    score_descriptor_against_prototype,
)
from src.inference.pipeline import TranslationPipeline
from src.nlp.translator import translate_glosses

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BANKS_DIR = PROJECT_ROOT / "models" / "gestures"
# Los bancos derivan de medios sin permiso documentado (MEDIA-DEBT-01): no se publican en Git.
BANKS_PRESENT = all((BANKS_DIR / f"{name}_bank.json").is_file() for name in ("numbers", "alphabet", "months"))
NEEDS_BANKS = unittest.skipUnless(BANKS_PRESENT, "Bancos de medios locales ausentes (MEDIA-DEBT-01)")


class TestMediaBankAndExtendedVocabulary(unittest.TestCase):
    @NEEDS_BANKS
    def test_step1_numbers_bank_and_translation(self):
        path = BANKS_DIR / "numbers_bank.json"
        self.assertTrue(path.is_file(), "Debe existir numbers_bank.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["classes"], NUMBER_ACTIONS)
        self.assertGreaterEqual(data["prototype_count"], 20)
        covered = {proto["gloss"] for proto in data["prototypes"]}
        self.assertEqual(covered, set(NUMBER_ACTIONS))

        # Traducción individual y secuencia de números
        self.assertEqual(translate_glosses(["1"])["text"], "Uno.")
        self.assertEqual(translate_glosses(["20"])["text"], "Veinte.")
        self.assertEqual(translate_glosses(["1", "5"])["text"], "Uno, cinco.")

        # Cada prototipo del banco debe lograr score >= 0.85 consigo mismo
        for proto in data["prototypes"]:
            self.assertGreaterEqual(score_descriptor_against_prototype(proto, proto), 0.85)

    @NEEDS_BANKS
    def test_step2_alphabet_bank_and_fingerspelling(self):
        path = BANKS_DIR / "alphabet_bank.json"
        self.assertTrue(path.is_file(), "Debe existir alphabet_bank.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["classes"], ALPHABET_ACTIONS)
        covered = {proto["gloss"] for proto in data["prototypes"]}
        self.assertEqual(covered, set(ALPHABET_ACTIONS))

        # Letra individual y deletreo de palabra completa
        self.assertEqual(translate_glosses(["A"])["text"], "Letra A.")
        self.assertEqual(translate_glosses(["Ñ"])["text"], "Letra Ñ.")
        self.assertEqual(translate_glosses(["H", "O", "L", "A"])["text"], "Hola.")
        self.assertEqual(translate_glosses(["P", "E", "R", "U"])["text"], "Peru.")

    @NEEDS_BANKS
    def test_step3_months_bank_complete_and_abbreviated_variants(self):
        path = BANKS_DIR / "months_bank.json"
        self.assertTrue(path.is_file(), "Debe existir months_bank.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["classes"], MONTH_ACTIONS)
        variants = {(proto["gloss"], proto.get("motion_kind")) for proto in data["prototypes"]}
        for month in MONTH_ACTIONS:
            self.assertIn((month, "dynamic_bimanual"), variants)
            self.assertIn((month, "rotated_initial"), variants)

        # Traducción de mes individual y fecha combinada con número
        self.assertEqual(translate_glosses(["OCTUBRE"])["text"], "Octubre.")
        self.assertEqual(translate_glosses(["20", "OCTUBRE"])["text"], "20 de octubre.")
        self.assertEqual(translate_glosses(["OCTUBRE", "20"])["text"], "20 de octubre.")

    def test_canonical_hand_pose_mirror_invariance(self):
        rng = np.random.default_rng(7)
        hand = rng.uniform(0.2, 0.8, size=(21, 3)).astype(np.float32)
        mirrored = hand.copy()
        mirrored[:, 0] = 1.0 - mirrored[:, 0]
        pose_right = canonical_hand_pose(hand)
        pose_left = canonical_hand_pose(mirrored)
        np.testing.assert_allclose(pose_right, pose_left, atol=1e-5)

    @NEEDS_BANKS
    def test_engine_pipeline_recognizes_and_flushes(self):
        # Construir una mano sintética y usar su propio descriptor como prototipo de "1"
        vec = np.zeros(126, dtype=np.float32)
        hand = vec[:63].reshape(21, 3)
        hand[0] = (0.5, 0.8, 0.0)
        hand[9] = (0.5, 0.65, 0.0)
        hand[8] = (0.5, 0.45, 0.0)
        hand[6] = (0.5, 0.68, 0.0)
        pose = canonical_hand_pose(hand).tolist()
        custom_bank = PROJECT_ROOT / "models" / "gestures" / "numbers_bank.json"
        engine = MediaSignBankEngine(categories=("numbers",), bank_paths=[custom_bank])
        engine.prototypes = [{
            "gloss": "1",
            "category": "numbers",
            "motion_kind": "static",
            "pose_mean": pose,
            "pose_start": pose,
            "pose_end": pose,
            "secondary_mean": [0.0] * len(pose),
            "pose_change": 0.0,
            "finger_jitter": 0.0,
            "wrist_range_x": 0.0,
            "wrist_range_y": 0.0,
            "wrist_reversals": 0,
            "bimanual_ratio": 0.0,
        }]
        pipeline = TranslationPipeline(engine)
        last = None
        for idx in range(15):
            last = pipeline.push(idx, idx * 80, vec)
        self.assertEqual(pipeline.confirmed_text, "Uno.")
        self.assertEqual(last["confirmed_text"], "Uno.")


if __name__ == "__main__":
    unittest.main()
