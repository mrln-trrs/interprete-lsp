# Intérprete de Lengua de Señas Peruana (LSP)

Prototipo académico LSP → glosas → español, con vocabulario cerrado de nueve clases. Implementa detección de manos, captura y carga segura de muestras, arquitectura LSTM/GRU, entrenamiento, inferencia temporal, reglas de estabilidad, plantillas, API con sesiones y UI con voz local opcional. **No contiene un modelo entrenado ni acredita reconocimiento real de señas.**

## Estado y planificación

El [plan maestro](docs/PLAN-INTERPRETE-LSP.md) adapta los [prompts del proyecto](<Prompts Maestros Integrales del Proyecto LSP.md>). El [Kanban](KANBAN.md) registra inicio, alcance, dependencias y límites de cada tarea mediante sus fichas de ejecución. La [auditoría](docs/quality/ISO-25010-AUDIT-REPORT.md) mantiene el dictamen **NO APTO para release o exposición pública**: corpus insuficiente y vulnerabilidad alta de protobuf abierta.

Por decisión del usuario, Arduino es una implementación futura opcional. La referencia lingüística inicial es el libro oficial de MINEDU; la revisión con asesor se registra como [deuda técnica](docs/TECHNICAL-DEBT.md). Se aprovechan fuentes gratuitas respetando sus permisos. Las plantillas actuales son exploratorias.

## Entorno reproducible

Python 3.11. Dependencias directas en `requirements.txt`; perfiles completos con hashes en `requirements.lock` (Windows) y `requirements-linux.lock` (Linux).

```powershell
py -3.11 -m venv venv_lsp
.\venv_lsp\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
```

```bash
python3.11 -m venv venv_lsp
venv_lsp/bin/python -m pip install --require-hashes -r requirements-linux.lock
```

En este Windows, el control de aplicaciones bloquea DLL SSL/optree; no se desactivaron esos controles. El perfil Linux fue validado por CI, incluyendo runtime TensorFlow/Keras, LSTM/GRU y guardado/carga. Consulta [ENV-03](docs/execution/ENV-03.md).

## Demo local

Configura `LSP_ACCESS_KEY` con un secreto de al menos 32 caracteres; la plantilla `.env.example` no se carga automáticamente. Ejecuta:

```powershell
.\venv_lsp\Scripts\python.exe web_server.py --host 127.0.0.1 --port 5000
```

Abre `http://127.0.0.1:5000`, ingresa la clave y autoriza tu cámara. Sin `--model-dir` la UI muestra ausencia de modelo y únicamente detección. Un artefacto compatible se carga explícitamente con esa opción. El servidor de desarrollo no acredita despliegue público. Para otro origen se exige `LSP_ALLOWED_ORIGINS` exacto.

La API usa `POST /api/v1/sessions`, `POST /api/v1/process-frame`, limpieza y cierre de sesión. El endpoint antiguo `/process_frame` devuelve 410. Consulta el [contrato](docs/backend/API-CONTRACTS.md). La cámara se libera al detener; no se persiste la clave ni se guarda video por defecto.

## Datos y entrenamiento

```bash
python -m src.dataset.record_samples --gloss HOLA --participant participante-01 --consent-ref consentimiento-local --samples 30
python -m src.training.train --dry-run
```

El primer comando requiere consentimiento real y cámara; la referencia de ejemplo no lo proporciona. Las muestras quedan pendientes de revisión. El loader verifica manifiesto, hashes y procedencia y separa por participante. El dry-run informa cobertura sin entrenar ni inventar métricas; falla si no hay corpus válido. El entrenamiento requiere cuotas por clase y splits completos; `--allow-unreviewed` únicamente permite exploración, sin aprobar release. Consulta [datos](docs/data/DATASET-PLAN.md), [fuentes gratuitas](docs/data/OPEN-SOURCES.md) y [entrenamiento](docs/ml/TRAINING-PLAN.md).

PERUSIL ofrece anotaciones abiertas, pero la cobertura comprobada no satisface las nueve clases. La descarga RGB local está truncada y no se acepta como corpus. No se ejecutó entrenamiento real.

## Verificación

```bash
python -m unittest discover -s tests -v
python -m scripts.check_contrast
```

CI Linux: 43 tests aprobados, smoke nativo y contraste aprobado. Windows: 42 aprobados y un test de ML omitido por política local. Las pruebas sintéticas validan software, no precisión lingüística. Navegador, cámara real, voz, Prolog y benchmark de latencia conservan límites explícitos en [QA-01](docs/execution/QA-01.md).

## Organización

`src/vision`: detección/normalización/re-muestreo; `src/dataset`: captura, loader e importación; `src/training`: modelos y entrenamiento; `src/inference`: ventanas y artefactos; `src/logic`: reglas Python y spike Prolog; `src/nlp`: plantillas/pipeline; `src/backend`: contratos y sesiones; `static`: UI; `tests`: suite; `scripts`: auditoría/contraste; `docs`: plan, evidencia y ejecución. `src/hardware` y `arduino` conservan la implementación preliminar diferida. Datos privados, entornos y modelos entrenados están excluidos de Git.
