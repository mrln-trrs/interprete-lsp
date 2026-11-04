#!/usr/bin/env bash
# Entrena el intérprete con el corpus PeruSIL (PUCP, CC0) de punta a punta. Cada fase se puede repetir:
# las descargas se reanudan y la importación salta las muestras ya guardadas.
#   docker compose run --rm lsp bash scripts/entrenar_perusil.sh
# Variables opcionales: SALIDA (models/perusil), EPOCAS (100), MIN_PARTICIPANTES (10), EXCLUIR ("GLOSA1 GLOSA2").
set -euo pipefail
SALIDA="${SALIDA:-models/perusil}"
EPOCAS="${EPOCAS:-100}"
CORPUS=data/keypoints_perusil
VOCAB=config/vocabularies/perusil.json

echo "== 1/6 Anotaciones y tabla de participantes (~200 KB)"
python -m src.dataset.perusil descargar --que anotaciones
echo "== 2/6 Plan: vocabulario y clips"
python -m src.dataset.perusil plan --min-participants "${MIN_PARTICIPANTES:-10}" --excluir ${EXCLUIR:-}
echo "== 3/6 Videos (~1.08 GB, reanudable) y extracción de los originales"
python -m src.dataset.perusil descargar --que videos
python -m src.dataset.perusil extraer
echo "== 4/6 Keypoints: ventana de 1 s centrada en cada seña"
python -m src.dataset.perusil importar --root "$CORPUS" --aceptar-anotacion-fuente
echo "== 5/6 Validación del corpus (sin entrenar)"
python -m src.training.train --root "$CORPUS" --vocabulary "$VOCAB" --dry-run
echo "== 6/6 Entrenamiento LSTM/GRU y evaluación única del test reservado"
python -m src.training.train --root "$CORPUS" --vocabulary "$VOCAB" --output "$SALIDA" --epochs "$EPOCAS" --evaluate-test
echo "Listo. Demo: python web_server.py --host 0.0.0.0 --model-dir $SALIDA  (con LSP_ALLOWED_ORIGINS si es remoto)"
