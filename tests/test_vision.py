"""
tests/test_vision.py
Pruebas unitarias para el detector MediaPipe y normalización espacial.
"""

import unittest
import numpy as np
from src.vision.mediapipe_detector import HandDetector
from src.vision.normalization import normalize_hand_landmarks, normalize_keypoints_vector


class TestVisionModule(unittest.TestCase):
    def setUp(self):
        self.detector = HandDetector(static_image_mode=True)

    def tearDown(self):
        self.detector.close()

    def test_detector_initialization(self):
        self.assertIsNotNone(self.detector.hands)
        self.assertEqual(self.detector.TOTAL_FEATURE_DIM, 126)

    def test_process_blank_frame(self):
        # Frame negro sintético sin manos
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = self.detector.process_frame(blank_frame)
        self.assertIsNone(results.multi_hand_landmarks)

        # Extracción sobre frame vacío debe retornar vector de 126 ceros
        keypoints = self.detector.extract_keypoints(results)
        self.assertEqual(keypoints.shape, (126,))
        self.assertTrue(np.all(keypoints == 0))

    def test_normalization_zeros(self):
        zeros_vec = np.zeros(126, dtype=np.float32)
        norm_vec = normalize_keypoints_vector(zeros_vec)
        self.assertEqual(norm_vec.shape, (126,))
        self.assertTrue(np.all(norm_vec == 0))

    def test_normalization_dummy_hand(self):
        # Simular una mano con 21 puntos
        dummy_hand = np.random.rand(21, 3).astype(np.float32) * 100.0
        norm_hand = normalize_hand_landmarks(dummy_hand)
        
        # La muñeca (índice 0) debe ser exactamente (0, 0, 0)
        np.testing.assert_almost_equal(norm_hand[0], [0.0, 0.0, 0.0], decimal=5)
        # Los puntos deben estar en un rango normalizado
        self.assertLessEqual(np.max(np.abs(norm_hand)), 10.0)


if __name__ == "__main__":
    unittest.main()
