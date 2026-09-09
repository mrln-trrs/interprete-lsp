"""
config/actions.py
Definición centralizada del vocabulario de Lengua de Señas Peruana (LSP).
"""

# Lista ordenada de clases aprendidas por el modelo
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

# Mapa de índice a texto legible
LABEL_MAP = {idx: label for idx, label in enumerate(ACTIONS)}

# Mapa inverso (texto a índice para etiquetado durante entrenamiento)
INVERSE_LABEL_MAP = {label: idx for idx, label in enumerate(ACTIONS)}

NUM_CLASSES = len(ACTIONS)
