import unittest
import numpy as np
from src.inference.handshape import HandshapeSentenceEngine, read_handshape
from src.inference.pipeline import TranslationPipeline


def shape_vector(pattern, x=0.5, y=0.8, bent=False):
    """Mano sintética: cada dígito del patrón indica si el dedo está extendido."""
    points = np.zeros((2, 21, 3))
    hand = points[0]
    hand[:] = (x, y, 0)
    hand[9, 1] = y - 0.15
    for flag, (tip, pip) in zip(pattern, ((8, 6), (12, 10), (16, 14), (20, 18))):
        hand[pip, 1] = y - 0.2
        hand[tip, 1] = y - ((0.21 if bent else 0.28) if flag == "1" else 0.16)
    return points.ravel()


class TestHandshapeSentences(unittest.TestCase):
    def feed(self, pipeline, script, frames=13):
        texts, accepted, frame = [], [], 0
        for pattern in script:
            for _ in range(frames):
                vector = np.zeros(126) if pattern is None else shape_vector(pattern)
                result = pipeline.push(frame, frame * 80, vector)
                frame += 1
                if result["prediction"] and result["prediction"]["accepted_gloss"]:
                    accepted.append(result["prediction"]["accepted_gloss"])
                if result["translation"] and result["translation"]["text"]:
                    texts.append(result["translation"]["text"])
        return texts, accepted

    def test_patterns(self):
        self.assertEqual(read_handshape(shape_vector("1100").reshape(2, 21, 3)[0])[0], "1100")
        self.assertEqual(read_handshape(shape_vector("0000").reshape(2, 21, 3)[0])[0], "0000")

    def test_full_sentence_goes_through_validator_and_templates(self):
        pipeline = TranslationPipeline(HandshapeSentenceEngine())
        texts, accepted = self.feed(pipeline, ["1000", "1100", "1110", None])
        self.assertEqual(accepted, ["YO", "QUERER", "AGUA"])
        self.assertEqual(texts, ["Yo quiero agua."])

    def test_other_phrases(self):
        pipeline = TranslationPipeline(HandshapeSentenceEngine())
        texts, _ = self.feed(pipeline, ["0000", "0001", None, "1001", None])
        self.assertEqual(texts, ["Ayuda, por favor.", "Gracias."])

    def test_short_or_unclear_gesture_is_not_accepted(self):
        pipeline = TranslationPipeline(HandshapeSentenceEngine())
        _, accepted = self.feed(pipeline, ["1000"], frames=6)  # menos de 10 cuadros
        self.assertEqual(accepted, [])
        engine = HandshapeSentenceEngine()
        result = engine.push(0, 0, shape_vector("1000", bent=True))  # dedo a medio doblar
        self.assertLess(result["prediction"]["confidence"], 0.85)

    def test_open_hand_still_is_neutral(self):
        engine = HandshapeSentenceEngine()
        self.assertIsNone(engine.push(0, 0, shape_vector("1111"))["prediction"])


if __name__ == "__main__":
    unittest.main()
