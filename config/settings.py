"""
config/settings.py
Constantes globales para ventanas de tiempo, frecuencias y hardware.
"""

# Parámetros temporales de captura e inferencia
TARGET_FPS = 30
SEQUENCE_LENGTH = 30           # 30 cuadros = 1 segundo de movimiento continuo

# Parámetros de detección
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Lógica de decisión
PREDICTION_THRESHOLD = 0.85    # Confianza mínima (85%) para aceptar una seña
STABILITY_FRAMES = 10          # Cuadros consecutivos requeridos para confirmar

# Configuración Arduino
SERIAL_PORT = "COM3"           # Ajustar según SO (ej. "/dev/ttyUSB0" en Linux)
BAUD_RATE = 9600
ENABLE_HARDWARE = False        # Cambiar a True cuando Arduino esté conectado
