from src.logic.validator import GlossValidator
from src.nlp.translator import TranslationBuffer


class TranslationPipeline:
    def __init__(self, engine):
        self.engine = engine
        self.validator = GlossValidator()
        self.buffer = TranslationBuffer()
        self.confirmed_text = ""

    def push(self, frame_id, timestamp_ms, raw_vector):
        inference = self.engine.push(frame_id, timestamp_ms, raw_vector)
        decision = self.validator.update(inference["prediction"], frame_id, timestamp_ms)
        if decision["gloss"]:
            self.buffer.append(decision["gloss"], timestamp_ms)
        translation = None
        if self.buffer.glosses and (decision["status"] == "rest" or self.buffer.due(timestamp_ms)
                                  or (decision["gloss"] and getattr(self.engine, "immediate_translation", False))):
            translation = self.buffer.flush()
            if translation["text"]:
                self.confirmed_text = translation["text"]
        candidate = inference["prediction"]
        if candidate:
            candidate = {**candidate, "status": decision["status"], "stable_frames": decision["stable_frames"],
                         "accepted_gloss": decision["gloss"]}
        return {"prediction": candidate, "translation": translation,
                "confirmed_text": self.confirmed_text, "pending_glosses": list(self.buffer.glosses),
                "ui_state": inference["state"], "reason": inference["reason"],
                "model_available": self.engine.predictor is not None}
