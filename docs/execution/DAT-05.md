# DAT-05 — Corpus PeruSIL y vocabulario configurable

Inicio: 2026-11-03; base `43c6958`. Estado: **código listo y probado; descarga de videos, importación y entrenamiento pendientes de ejecutar en otra PC**.

## Por qué

El corpus propio de las 9 glosas base (DAT-03) no existe todavía. PeruSIL (PUCP-DGI156, licencia CC0 1.0, `hdl:20.500.12534/OJYYYS`) trae 27 videos de 17 participantes con anotación experta por seña (`SRT_SEGMENTED_SIGN`). Permite entrenar con **señas reales** ya, aunque con otro vocabulario: de las 9 glosas base, solo YO alcanza 30 ejemplos.

## Vocabulario elegido (`config/vocabularies/perusil.json`)

`python -m src.dataset.perusil plan` sobre las anotaciones (SRT.tar, MD5 `f31f59c5…`, y la tabla de participantes) eligió **12 glosas y 655 clips**. Para entrar, cada glosa necesita al menos 30 clips, 10 participantes y presencia en train, validation y test con la misma partición (semilla 42) que usa `split_dataset`. Una prueba verifica que la simulación y el cargador reparten igual.

| Glosa | Clips | Participantes |
|---|---|---|
| PENSAR | 98 | 13 |
| MUJER | 89 | 14 |
| HOMBRE | 73 | 13 |
| YO | 73 | 14 |
| CAMINAR | 48 | 14 |
| TU | 47 | 10 |
| NO | 44 | 11 |
| DOS | 43 | 10 |
| QUE? | 39 | 14 |
| YA | 37 | 11 |
| CASA | 32 | 10 |
| SI | 32 | 12 |

Partición por persona:

| Partición | Participantes |
|---|---|
| Entrenamiento | 10: p01, p04, p07, p08, p10, p11, p12, p13, p16, p17 |
| Validación | 3: p03, p05, p06 |
| Prueba | 4: p02, p09, p14, p15 |

Descartados: 309 clips en tramos con movimiento de cámara (marcados en la tabla del corpus) y 2 cuyas ventanas empezaban antes del inicio del video.

## Decisiones

1. **Ventana de 1 s centrada en la seña.** Las señas anotadas duran entre 0.3 y 0.9 s (mediana de unos 450 ms). Se toma la ventana de 1 s centrada en el punto medio, que incluye algo del contexto anterior y posterior. No se estiran ni repiten clips. Es un cambio de método respecto a la captura propia (1 s grabado a propósito) y debe evaluarse con los resultados.
2. **Revisión.** Con `--aceptar-anotacion-fuente`, las muestras quedan `reviewed` con `review_ref` igual a la anotación del corpus: la anotación experta de la PUCP cumple el papel de revisión humana. Sin esa opción quedan `unreviewed`.
3. **Procedencia.** `source=perusil-pucp-dgi156`, `consent_ref=CC0-1.0 PUCP-DGI156 (hdl:…)` y `origin` con video, intervalo, glosa y dataset, para auditar cada muestra.
4. **Espejo.** Los cuadros se espejan antes de MediaPipe (`mediapipe-selfie-input`), igual que `record_samples` y `public_import`.
5. **Sin REPOSO.** PeruSIL son relatos continuos, sin reposo etiquetado. El motor detecta que el vocabulario no tiene REPOSO y muestra cada glosa aceptada al momento (traducción inmediata, lectura literal: «Mujer pensar.»).
6. **Videos fuera de Git.** `data/raw_videos/`, `data/keypoints_*/` y `models/perusil/` están en `.gitignore`. Se versionan el código, el vocabulario y este registro.

## Cambios de código

| Archivo | Cambio |
|---|---|
| `src/vocabulary.py` (nuevo) | Carga y valida vocabularios; carpeta segura para glosas con `?` |
| `src/dataset/perusil.py` (nuevo) | Fases `descargar` (reanudable, verifica tamaño y MD5), `plan`, `extraer` (sin rutas del tar) e `importar` (reanuda) |
| `src/dataset/record_samples.py` | `allowed_glosses`, `quality_status` con `review_ref` y `origin` |
| `src/dataset/dataset_loader.py` | `classes` y `--vocabulary` |
| `src/training/model_builder.py` | Número de clases según el vocabulario; unidades, densa, L2 y tasa de aprendizaje como parámetros |
| `src/training/train.py` | `--vocabulary`; hiperparámetros por CLI (`--units`, `--dropout`, `--l2`, `--learning-rate`, `--batch-size`, `--patience`, `--dense-units`); el metadata guarda hiperparámetros, corpus y métricas de validación |
| `src/inference/engine.py` | El modelo fija su vocabulario (`class_order` debe coincidir con el encoder); traducción inmediata sin REPOSO |
| `src/logic/validator.py`, `src/inference/pipeline.py`, `src/nlp/translator.py` | Validan y nombran glosas con el vocabulario del motor; lectura literal para glosas sin plantilla |
| `web_server.py` | **Corrección:** espeja el cuadro antes de MediaPipe. Antes, la captura y los importadores espejaban y el servidor no, así que un modelo entrenado habría visto las manos invertidas en la demo |
| `Dockerfile`, `docker-compose.yml`, `scripts/entrenar_perusil.sh` | Entorno y ejecución de punta a punta en cualquier PC |

## Validación

Suite completa en contenedor Linux con `LSP_NATIVE_ML_TESTS=1`. Nuevas pruebas en `tests/test_vocabulary.py` y `tests/test_perusil.py`:

- vocabulario: validación, carpetas seguras y configuración del modelo según el número de clases;
- cargador y partición con clases propias;
- motor, validador, orquestador y traductor con un vocabulario sin REPOSO;
- lectura de la tabla y de los SRT, exclusión de los tramos con movimiento de cámara y cobertura en las tres particiones;
- igualdad entre la partición simulada del plan y la del cargador.

## Pendiente (otra PC)

```bash
docker compose build
docker compose run --rm lsp bash scripts/entrenar_perusil.sh
```

Después:

1. Si alguna clase queda con menos de 30 muestras tras la importación, rehacer el plan con `EXCLUIR="GLOSA"`.
2. Registrar las métricas de validación y de test, la matriz de confusión y el baseline mayoritario en una ficha MOD-03.
3. Probar el modelo en la demo con `--model-dir models/perusil`.
