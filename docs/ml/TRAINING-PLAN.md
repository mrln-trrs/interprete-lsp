# Entrenamiento y evaluación recurrente

Fecha: 2026-10-06. `model_builder.py` y `train.py` pendientes; no hay métricas de reconocimiento demostradas.

| Parámetro | Baseline propuesto | Selección |
|---|---|---|
| Entrada | `(30,126)` float32, esquema congelado | Cambios requieren versión |
| Clases | 9, orden exacto de ACTIONS | Encoder vinculado al modelo |
| Red | LSTM 64 → Dropout 0.3 → Dense 32 ReLU → Softmax 9 | Comparar GRU 64 con mismo presupuesto |
| Regularización | L2 1e-4; dropout 0.3 | Solo validation |
| Optimizador | Adam, learning rate 1e-3 | Reducir si validation se estanca |
| Pérdida | Sparse categorical crossentropy | Etiquetas enteras; no mezclar one-hot |
| Batch / épocas | 16 / máximo 100 | EarlyStopping patience 10 |
| Checkpoint | Mejor validation loss, restaurar pesos | Test reservado |
| Reproducibilidad | Semillas 42, versiones y configuración registradas | Indicar operaciones no deterministas |

Pipeline: verificar corpus/manifiesto y hashes → usar splits por participante → entrenar baseline → seleccionar con validation → evaluar test reservado → guardar modelo, encoder y metadata → round-trip y benchmark de inferencia. Mínimo comparar predictor mayoritario y LSTM/GRU; no aumentar capas si el corpus no lo justifica. Registrar curvas train/validation y posibles desbalances.

Métricas: accuracy, precision/recall/F1 por clase, macro-F1, soporte y matriz de confusión con orden explícito. Reportar resultados por participante/sesión y tasa de falsa aceptación en REPOSO y gestos no incluidos. Meta propuesta: macro-F1 ≥0.85, recall por clase ≥0.70 y falsas emisiones ≤1 por minuto en cinco minutos de reposo/gestos fuera de vocabulario. Confianza softmax no equivale a certeza calibrada; revisar calibración en validation y sensibilidad a umbral 0.85 antes de aceptar.

Artefactos locales: `models/trained/lsp_model.keras` candidato principal, `lstm_lsp_model.h5` si se requiere compatibilidad comprobada, `label_encoder.json`, `metadata.json`, reporte y hashes. ADR-09 adapta el formato del prompt; no instalar/actualizar Keras solo para elegir extensión. Metadata incluye versiones Python/librerías, commit, schema, normalización, orden de clases, semilla, split/hash corpus, hiperparámetros y métricas. Evitar publicar metadata con IDs de participantes.

Inferencia rechaza modelo/encoder/esquema incompatibles. Cargar modelo de procedencia aprobada; test round-trip compara predicciones con tolerancia 1e-5 sobre fixture independiente. Registrar tamaño, tiempo de carga y latencia p50/p95; la inferencia más lenta degrada cadencia con aviso y descarta frames antiguos. `python -m src.training.train` será comando futuro al implementar; hoy no entrena.
