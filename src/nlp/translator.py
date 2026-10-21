"""
src/nlp/translator.py
Módulo de traducción de secuencias de glosas LSP a español natural coherente.
Soporta vocabulario base, números (1-20), dactilología (A-Z, Ñ) y meses del año.
"""
from config.actions import (
    ACTIONS,
    ALPHABET_ACTIONS,
    EXTENDED_ACTIONS,
    MONTH_ACTIONS,
    NUMBER_ACTIONS,
)

GLOSSARY_VERSION = "es-templates-exploratory-v2"

NUMBER_NAMES = {
    "1": "Uno", "2": "Dos", "3": "Tres", "4": "Cuatro", "5": "Cinco",
    "6": "Seis", "7": "Siete", "8": "Ocho", "9": "Nueve", "10": "Diez",
    "11": "Once", "12": "Doce", "13": "Trece", "14": "Catorce", "15": "Quince",
    "16": "Dieciséis", "17": "Diecisiete", "18": "Dieciocho", "19": "Diecinueve", "20": "Veinte",
}

MONTH_NAMES = {
    "ENERO": "enero", "FEBRERO": "febrero", "MARZO": "marzo", "ABRIL": "abril",
    "MAYO": "mayo", "JUNIO": "junio", "JULIO": "julio", "AGOSTO": "agosto",
    "SETIEMBRE": "setiembre", "OCTUBRE": "octubre", "NOVIEMBRE": "noviembre", "DICIEMBRE": "diciembre",
}

TEMPLATES = {
    ("HOLA",): "Hola.",
    ("GRACIAS",): "Gracias.",
    ("POR_FAVOR",): "Por favor.",
    ("AYUDA",): "Ayuda.",
    ("AGUA",): "Agua.",
    ("BUENOS_DIAS",): "Buenos días.",
    ("YO", "QUERER", "AGUA"): "Yo quiero agua.",
}

for _num, _name in NUMBER_NAMES.items():
    TEMPLATES[(_num,)] = f"{_name}."

for _letter in ALPHABET_ACTIONS:
    TEMPLATES[(_letter,)] = f"Letra {_letter}."

for _month, _mname in MONTH_NAMES.items():
    TEMPLATES[(_month,)] = f"{_mname.capitalize()}."


def _compose_dynamic_template(filtered):
    if not filtered:
        return None
    if filtered in TEMPLATES:
        return TEMPLATES[filtered]
    # Deletreo dactilológico: 2 o más letras consecutivas forman palabra
    if len(filtered) >= 2 and all(g in ALPHABET_ACTIONS for g in filtered):
        word = "".join(filtered).lower().capitalize()
        return f"{word}."
    # Fecha: Número + Mes o Mes + Número (ej. ("20", "OCTUBRE") -> "20 de octubre.")
    if len(filtered) == 2:
        first, second = filtered
        if first in NUMBER_NAMES and second in MONTH_NAMES:
            return f"{first} de {MONTH_NAMES[second]}."
        if first in MONTH_NAMES and second in NUMBER_NAMES:
            return f"{second} de {MONTH_NAMES[first]}."
    # Secuencia de números (ej. ("1", "5") -> "Uno, cinco.")
    if len(filtered) >= 2 and all(g in NUMBER_NAMES for g in filtered):
        parts = [NUMBER_NAMES[g].lower() for g in filtered]
        parts[0] = parts[0].capitalize()
        return ", ".join(parts) + "."
    return None


def translate_glosses(glosses):
    if not isinstance(glosses, (list, tuple)) or len(glosses) > 20 or any(gloss not in EXTENDED_ACTIONS for gloss in glosses):
        raise ValueError("Secuencia de glosas no permitida")
    filtered = tuple(gloss for gloss in glosses if gloss != "REPOSO")
    text = _compose_dynamic_template(filtered)
    return {
        "text": text,
        "source_glosses": list(filtered),
        "glossary_version": GLOSSARY_VERSION,
        "status": "Empty" if not filtered else "Success" if text else "Partial",
        "message": None if text or not filtered else "Sin plantilla disponible",
        "linguistic_review": "pending",
    }


class TranslationBuffer:
    def __init__(self):
        self.glosses = []
        self.started_at_ms = None

    def append(self, gloss, timestamp_ms):
        if gloss not in EXTENDED_ACTIONS or gloss == "REPOSO":
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
