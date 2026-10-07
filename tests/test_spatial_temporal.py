import unittest
import numpy as np
from src.vision.normalization import normalize_hand_landmarks, normalize_keypoints_vector
from src.vision.temporal import resample_sequence


class TestSpatialTemporal(unittest.TestCase):
    def test_invariance_and_degenerate_hand(self):
        hand = np.arange(63, dtype=float).reshape(21, 3)
        expected = normalize_hand_landmarks(hand)
        np.testing.assert_allclose(expected, normalize_hand_landmarks(hand * 3.7 + [100, -5, 12]), atol=1e-5)
        np.testing.assert_array_equal(normalize_hand_landmarks(np.ones((21, 3))), np.zeros((21, 3)))
        self.assertEqual(expected.dtype, np.float32)

    def test_validation_and_absent_block(self):
        for vector in (np.zeros((126, 1)), np.full(126, np.nan), np.full(126, np.inf), np.zeros(125), np.zeros(126, dtype=bool)):
            with self.assertRaises(ValueError):
                normalize_keypoints_vector(vector)
        vector = np.concatenate([np.arange(63), np.zeros(63)])
        np.testing.assert_array_equal(normalize_keypoints_vector(vector)[63:], np.zeros(63))

    def test_fps_independent_duration(self):
        for count in (13, 31):
            timestamps = np.linspace(0, 1000, count)
            values = np.repeat(timestamps[:, None], 126, axis=1)
            sequence, grid = resample_sequence(values, timestamps)
            self.assertEqual(sequence.shape, (30, 126))
            np.testing.assert_allclose(sequence[:, 0], grid, rtol=1e-6)

    def test_temporal_gaps_and_order(self):
        for timestamps in ([0, 1000], [0, 100, 100], [0, 100, 200], [0, float("nan")]):
            with self.assertRaises(ValueError):
                resample_sequence(np.zeros((len(timestamps), 126)), timestamps)
