"""
src/main.py
Punto de entrada principal para inferencia y traducción en tiempo real.
"""

import sys
from pathlib import Path

# Garantizar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.mediapipe_detector import run_live_camera



def main():
    print("==================================================")
    print("   INTÉRPRETE DE LENGUA DE SEÑAS PERUANA (LSP)    ")
    print("           Módulo de Detección de Manos          ")
    print("==================================================")
    run_live_camera()


if __name__ == "__main__":
    main()

