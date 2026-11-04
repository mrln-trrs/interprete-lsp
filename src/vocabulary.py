"""
src/vocabulary.py
Vocabulario de clases de un modelo entrenado.

Por defecto el proyecto entrena las 9 glosas base de config/actions.py. Un corpus externo (por ejemplo
PeruSIL) define su propio vocabulario en un JSON {"classes": [...]} que acompaña al corpus, al modelo
(label_encoder.json) y al motor de inferencia, para que el orden de clases sea siempre el mismo.
"""
import json
import re
from pathlib import Path

from config.actions import ACTIONS

GLOSS_PATTERN = re.compile(r"[A-ZÁÉÍÓÚÜÑ0-9_?]{1,40}")


def validate_classes(classes):
    if not isinstance(classes, (list, tuple)) or not 2 <= len(classes) <= 200:
        raise ValueError("El vocabulario requiere entre 2 y 200 clases")
    if any(not isinstance(gloss, str) or not GLOSS_PATTERN.fullmatch(gloss) for gloss in classes):
        raise ValueError("Glosa no válida: use MAYÚSCULAS, dígitos, _ o ?")
    if len(set(classes)) != len(classes):
        raise ValueError("El vocabulario tiene glosas repetidas")
    return list(classes)


def load_vocabulary(path=None):
    """Lista ordenada de clases: la del archivo indicado o, sin archivo, las 9 glosas base."""
    if path is None:
        return list(ACTIONS)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_classes(data.get("classes") if isinstance(data, dict) else None)


def gloss_folder(gloss):
    """Nombre de carpeta seguro en cualquier sistema de archivos (el ? no es válido en Windows)."""
    return gloss.replace("?", "_Q")
