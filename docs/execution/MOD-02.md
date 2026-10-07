# MOD-02 — Pipeline de entrenamiento y evaluación

Inicio: 2026-10-06, después de MOD-01. Estado: parcial: pipeline implementado y métricas probadas; entrenamiento real pendiente.

Alcance: loader/split por persona, gate ≥30 muestras/clase, baseline LSTM/GRU con selección solo por validation, EarlyStopping, semillas, guardado `.keras`, encoder/metadata/hash, round-trip y test reservado abierto solo con `--evaluate-test`. Métricas NumPy: accuracy, precision/recall/F1 por clase, macro-F1, soporte y matriz. Mayoritario como baseline. Artefactos privados fuera de Git; nada se marca aprobado para release.

CLI inicial: `python -m src.training.train --dry-run`; permite `--allow-unreviewed` solo exploratorio. Sin manifiesto/cobertura válida falla antes de importar Keras. DAT-03 incompleto y ENV-03 bloqueado impiden entrenar; el dry-run no genera métricas falsas. Un directorio que abrió test no permite volver a abrirlo silenciosamente.

Validación: tres tests propios PASS de matriz conocida, etiquetas inválidas y dry-run sin métricas sobre fixture temporal; compilación sintáctica. No se ejecutaron fit, exportación ni round-trip reales. Implementar esos pasos no significa haber aprobado VAL-03. Las dependencias de datos/runtime siguen abiertas.
