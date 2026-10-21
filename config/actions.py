"""
config/actions.py
Definición centralizada del vocabulario de Lengua de Señas Peruana (LSP).
"""

# Lista ordenada de clases base aprendidas por el modelo (9 clases originales)
ACTIONS = [
    "REPOSO",       # Clase 0: Manos abajo o sin realizar gesto
    "HOLA",         # Clase 1
    "GRACIAS",      # Clase 2
    "POR_FAVOR",    # Clase 3
    "AYUDA",        # Clase 4
    "YO",           # Clase 5
    "QUERER",       # Clase 6
    "AGUA",         # Clase 7
    "BUENOS_DIAS"   # Clase 8
]

# Mapa de índice a texto legible (vocabulario base)
LABEL_MAP = {idx: label for idx, label in enumerate(ACTIONS)}

# Mapa inverso (texto a índice para etiquetado durante entrenamiento base)
INVERSE_LABEL_MAP = {label: idx for idx, label in enumerate(ACTIONS)}

NUM_CLASSES = len(ACTIONS)

# Vocabularios extendidos por categoría:
# 1. Números (1 al 20)
NUMBER_ACTIONS = [str(n) for n in range(1, 21)]

# 2. Abecedario dactilológico (A a Z + Ñ)
ALPHABET_ACTIONS = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "Ñ", "O", "P", "Q", "R", "S",
    "T", "U", "V", "W", "X", "Y", "Z"
]

# 3. Meses del año
MONTH_ACTIONS = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]

EXTENDED_ACTIONS = ACTIONS + NUMBER_ACTIONS + ALPHABET_ACTIONS + MONTH_ACTIONS
EXTENDED_LABEL_MAP = {idx: label for idx, label in enumerate(EXTENDED_ACTIONS)}
EXTENDED_INVERSE_LABEL_MAP = {label: idx for idx, label in enumerate(EXTENDED_ACTIONS)}
