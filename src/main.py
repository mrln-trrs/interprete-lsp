"""
src/main.py
Punto de entrada principal para inferencia y traducción en tiempo real.
"""

from src.vision.mediapipe_detector import run_live_camera


def main():
    print("==================================================")
    print("   INTÉRPRETE DE LENGUA DE SEÑAS PERUANA (LSP)    ")
    print("           Módulo de Detección de Manos          ")
    print("==================================================")
    run_live_camera()


if __name__ == "__main__":
    main()

