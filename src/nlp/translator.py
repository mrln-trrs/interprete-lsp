"""
src/nlp/translator.py
Módulo de traducción de secuencias de glosas LSP a español natural coherente.
"""
from config.actions import ACTIONS

GLOSSARY_VERSION = "es-templates-exploratory-v1"
TEMPLATES = {
    ("HOLA",): "Hola.", ("GRACIAS",): "Gracias.", ("POR_FAVOR",): "Por favor.",
    ("AYUDA",): "Ayuda.", ("AGUA",): "Agua.", ("BUENOS_DIAS",): "Buenos días.",
    ("YO", "QUERER", "AGUA"): "Yo quiero agua.",
}


def translate_glosses(glosses):
    if not isinstance(glosses, (list, tuple)) or len(glosses) > 20 or any(gloss not in ACTIONS for gloss in glosses):
        raise ValueError("Secuencia de glosas no permitida")
    filtered = tuple(gloss for gloss in glosses if gloss != "REPOSO")
    text = TEMPLATES.get(filtered)
    return {"text": text, "source_glosses": list(filtered), "glossary_version": GLOSSARY_VERSION,
            "status": "Empty" if not filtered else "Success" if text else "Partial",
            "message": None if text or not filtered else "Sin plantilla disponible",
            "linguistic_review": "pending"}


class TranslationBuffer:
    def __init__(self):
        self.glosses = []
        self.started_at_ms = None

    def append(self, gloss, timestamp_ms):
        if gloss not in ACTIONS or gloss == "REPOSO":
            raise ValueError("Solo glosas confirmadas no-REPOSO")
        if len(self.glosses) >= 20:
            raise ValueError("Límite de glosas; despachar antes de añadir")
        if self.started_at_ms is None:
            self.started_at_ms = timestamp_ms
        self.glosses.append(gloss)

    def due(self, timestamp_ms):
        return len(self.glosses) >= 20 or (self.started_at_ms is not None and timestamp_ms - self.started_at_ms >= 10000)

    def flush(self):
        result = translate_glosses(self.glosses)
        self.glosses = []
        self.started_at_ms = None
        return result
