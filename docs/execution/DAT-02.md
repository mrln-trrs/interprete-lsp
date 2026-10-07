# DAT-02 — Loader seguro y partición por participante

Inicio: 2026-10-06, después de DAT-01. Estado: Done para software y pruebas estructurales.

Alcance: carga exclusiva desde manifiesto, rutas bajo raíz, rechazo de pickle/dimensiones/dtype/NaN/hash/versiones incompatibles; metadatos de permiso y participante obligatorios; reporte de exclusiones. Train/validation/test 60/20/20 aproximado por participantes, semilla 42, mínimo cinco grupos y cobertura de nueve clases en cada split. No se admiten archivos huérfanos.

CLI: `python -m src.dataset.dataset_loader --root data/keypoints`. Por defecto exige `quality_status=reviewed`; `--allow-unreviewed` es una opción explícita de prototipo, sin aprobar revisión lingüística. No inventar revisión en manifiesto para pasar el gate.

Validación: tres tests PASS: fixture temporal de 45 matrices (cinco grupos × nueve etiquetas) prueba disjunción; corrupción/ausencia de revisión, path traversal y pocos grupos se rechazan. Estos ceros son fixtures sintéticos, no señas ni entrenamiento.

Límite: no corpus real ni cuotas de 30–50 secuencias. DAT-03 aún debe verificar cobertura y calidad de fuentes abiertas. VAL-02 no se aprueba con los tests del loader.
