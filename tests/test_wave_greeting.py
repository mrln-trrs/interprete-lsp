import unittest
import numpy as np
from src.inference.wave import WaveGreetingEngine
from src.inference.pipeline import TranslationPipeline


def hand_vector(x, opened=True, slot=0, y=0.8):
    points = np.zeros((2, 21, 3))
    hand = points[slot]
    hand[:] = (x, y, 0)
    hand[9, 1] = y - 0.15
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        hand[pip, 1] = y - 0.2
        hand[tip, 1] = y - (0.35 if opened else 0.12)
    return points.ravel()


class TestWaveGreeting(unittest.TestCase):
    def feed(self, pipeline, xs, start=0, opened=True, slots=False):
        output = []
        for i, x in enumerate(xs, start):
            result = pipeline.push(i, i * 80, hand_vector(x, opened, i % 2 if slots else 0))
            if result['translation']:
                output.append(result['translation']['text'])
        return output

    def test_wave_translates_once_without_waiting_for_rest(self):
        pipeline = TranslationPipeline(WaveGreetingEngine())
        texts = self.feed(pipeline, 0.5 + 0.13 * np.sin(np.arange(60) * 0.5))
        self.assertEqual(texts, ['Hola.'])
        self.assertEqual(pipeline.confirmed_text, 'Hola.')

    def test_stationary_noise_and_single_sweep_do_not_translate(self):
        for xs in (np.full(45, 0.5), 0.5 + 0.01 * np.sin(np.arange(45)), np.linspace(0.3, 0.7, 45)):
            self.assertEqual(self.feed(TranslationPipeline(WaveGreetingEngine()), xs), [])

    def test_closed_hand_does_not_translate(self):
        xs = 0.5 + 0.13 * np.sin(np.arange(60) * 0.5)
        self.assertEqual(self.feed(TranslationPipeline(WaveGreetingEngine()), xs, opened=False), [])

    def test_detector_slot_changes_preserve_same_hand(self):
        xs = 0.5 + 0.13 * np.sin(np.arange(60) * 0.5)
        self.assertEqual(self.feed(TranslationPipeline(WaveGreetingEngine()), xs, slots=True), ['Hola.'])

    def test_lowering_hand_rearms_next_greeting(self):
        pipeline = TranslationPipeline(WaveGreetingEngine())
        xs = 0.5 + 0.13 * np.sin(np.arange(60) * 0.5)
        self.assertEqual(self.feed(pipeline, xs), ['Hola.'])
        for i in range(60, 80):
            pipeline.push(i, i * 80, np.zeros(126))
        self.assertEqual(self.feed(pipeline, xs, start=80), ['Hola.'])

    def test_gap_and_invalid_input_do_not_replay_gesture(self):
        engine = WaveGreetingEngine()
        for i in range(15):
            engine.push(i, i * 80, hand_vector(0.5 + 0.13 * np.sin(i * 0.5)))
        result = engine.push(15, 3000, hand_vector(0.5))
        self.assertEqual(result['prediction']['gloss'], 'REPOSO')
        with self.assertRaises(ValueError):
            engine.push(15, 3100, hand_vector(0.5))
        with self.assertRaises(ValueError):
            engine.push(16, 3100, np.full(126, np.nan))


if __name__ == '__main__':
    unittest.main()
