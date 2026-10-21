# MOD-02 — Pipeline de entrenamiento y evaluación

Inicio: 2026-10-06, después de MOD-01. Estado: parcial: pipeline implementado y métricas probadas; entrenamiento real pendiente.

Alcance: loader/split por persona, gate ≥30 muestras/clase, baseline LSTM/GRU con selección solo por validation, EarlyStopping, semillas, guardado `.keras`, encoder/metadata/hash, round-trip y test reservado abierto solo con `--evaluate-test`. Métricas NumPy: accuracy, precision/recall/F1 por clase, macro-F1, soporte y matriz. Mayoritario como baseline. Artefactos privados fuera de Git; nada se marca aprobado para release.

CLI inicial: `python -m src.training.train --dry-run`; permite `--allow-unreviewed` solo exploratorio. Sin manifiesto/cobertura válida falla antes de importar Keras. DAT-03 incompleto y ENV-03 bloqueado impiden entrenar; el dry-run no genera métricas falsas. Un directorio que abrió test no permite volver a abrirlo silenciosamente.

Validación: tres tests propios PASS de matriz conocida, etiquetas inválidas y dry-run sin métricas sobre fixture temporal; compilación sintáctica. No se ejecutaron fit, exportación ni round-trip reales. Implementar esos pasos no significa haber aprobado VAL-03. Las dependencias de datos/runtime siguen abiertas.

## Avance 2026-10-21

`tests/test_training_end_to_end.py` (con `LSP_NATIVE_ML_TESTS=1`) ejecuta el pipeline real sobre un corpus sintético separable de 10 participantes × 9 clases × 3 muestras: `run_training` entrena LSTM y GRU, selecciona por validación, guarda `.keras`, hace round-trip, abre el test reservado una sola vez (el segundo intento falla) y supera al baseline mayoritario; luego `load_predictor` + `InferenceEngine` reconocen la clase correcta en una ventana temporal y un artefacto alterado se rechaza por checksum. PASS en Linux aarch64 (OrbStack). `current_commit()` ya no falla sin git: registra `unknown`. Esto acredita el código, no la precisión con señas reales: el entrenamiento real sigue bloqueado por DAT-03.
