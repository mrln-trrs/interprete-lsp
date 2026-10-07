# Adquisición y gobierno del dataset

Fecha: 2026-10-06. Capturador y loader son stubs; corpus no verificado.

## Recolección

Orden: consentimiento → validación lingüística de las nueve clases → piloto de normalización/lateralidad → congelar esquema → capturar → validar → particionar por participante. Objetivo inicial 30–50 secuencias válidas por clase (270–450 total), con al menos cinco participantes si hay disponibilidad. Ese volumen es un punto de partida, no garantía de generalización. Incluir diversidad de sesiones, iluminación, distancia y dominancia; documentar limitaciones de representatividad sin recopilar atributos sensibles innecesarios.

Contrato futuro `record_samples.py`: seleccionar clase allowlist de `config/actions.py`, participante seudónimo y sesión; preflight; cuenta regresiva de dos segundos; capturar un segundo con timestamps; convertir a `(30,126)` float32; mostrar siete estados; confirmar/escribir atómicamente. Cancelar no guarda muestra. Nunca derivar rutas de glosas arbitrarias. Ruta `data/keypoints/<GLOSA>/seq_<ID_UNICO>.npy`; no sobrescribir archivos ni reiniciar contador silenciosamente.

## Manifiesto y validación

Manifiesto JSON local fuera de Git con `sample_id`, `relative_path`, `gloss`, `participant_id`, `session_id`, `consent_ref`, `schema_version`, `normalization_version`, `mirror_convention`, `capture_fps`, `timestamps_ms`, `duration_ms`, `shape`, `dtype`, `checksum_sha256`, `quality_status`, `split`. Timestamps corresponden a las 30 posiciones remuestreadas; preservar además resumen de captura original y hueco máximo. No incluir nombre, contacto ni video.

Loader futuro: `allow_pickle=False`; extensión/ruta bajo raíz autorizada; matriz exacta `(30,126)` float32 y finita; hash válido, etiqueta conocida, versión compatible; rechazar corrupción y emitir reporte de exclusiones. REPOSO incluye ausencia real y posiciones de descanso etiquetadas por asesor; un bloque cero es mano ausente, no inferir automáticamente clase fuera de contexto. Secuencias con huecos >200 ms, lateralidad ambigua o seguimiento perdido se revisan/rechazan antes de entrenamiento.

## Particiones sin fuga

Objetivo 60/20/20 train/validation/test por participante con semilla 42 y manifiesto congelado; adaptar números enteros preservando grupos y cobertura de todas las clases. Todas las sesiones de una persona quedan en una sola partición. No usar split aleatorio por frame/secuencia como sustituto. Con cinco participantes, reparto inicial 3/1/1; reportar incertidumbre por pequeño número de personas. Si faltan clases en una partición, recopilar más datos antes de medir aceptación.

Augmentation solo sobre train y después del split; no reflejar manos si cambia significado. Test se abre tras selección de arquitectura/umbrales en validation; resultados fallidos no se arreglan entrenando sobre test. Corpus nuevo requiere versión y nuevo test reservado.

## Privacidad y distribución

Consentimiento describe finalidad académica, acceso, datos derivados, revocación y borrado. Retención propuesta: hasta fin de evaluación académica más 30 días, máximo seis meses salvo renovación explícita; confirmar política antes de recolectar. Video no se guarda por defecto. Evidencia de consentimiento identificable separada del manifiesto, acceso restringido. Revocación elimina muestras y revisa modelos derivados antes de compartirlos.

Compartir archivo privado cifrado/controlado con checksum y manifiesto, nunca corpus identificable en GitHub Releases público. `.gitignore` ya excluye `data/keypoints/` y videos; futuras carpetas de metadatos, consentimientos y artefactos requieren exclusiones comprobadas antes de usarlas. README de dataset sin identidad puede versionarse. No recolectar ni cargar datos de personas durante este trabajo documental.

Comandos futuros, todavía no ejecutables por ser stubs: `python -m src.dataset.record_samples` y `python -m src.dataset.dataset_loader`. Documentar sus argumentos al implementar; no presentarlos como instrucciones funcionales actuales.
