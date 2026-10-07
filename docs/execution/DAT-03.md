# DAT-03 — Inspección de corpus abierto y brecha

Inicio: 2026-10-06; base `71eaa55`. Estado: **parcial**, corpus objetivo todavía insuficiente.

Se descargaron/inspeccionaron 27 anotaciones por seña del corpus PUCP/PeruSIL con licencia CC0. Hash y conteos en `docs/data/PERUSIL-COVERAGE.json`; script reproducible `python -m scripts.inspect_perusil`. Correspondencias textuales exactas: HOLA 4, GRACIAS 4, POR_FAVOR 6, YO 81, QUERER 15, AGUA 2; REPOSO/AYUDA/BUENOS_DIAS sin coincidencias. Son anotaciones, no muestras ya extraídas/validadas. Solo una anotación POR_FAVOR dura al menos un segundo; no se estiran o repiten artificialmente clips para alcanzar 30–50 muestras.

Se prepara importador local de intervalos explícitamente etiquetados y autorizados, sin pickle ni extracción insegura de archivos: `python -m src.dataset.public_import --index INDICE_CC0.json --videos-root CARPETA`. El índice incluye source, license=CC0-1.0, permission_ref y clips con video/gloss/start_ms/end_ms/participant_id/session_id. Conserva participantes, usa la misma normalización/ventana y guarda estado unreviewed. No inventar anotaciones, mapping semántico o consentimiento para completar clases.

Límite: todavía no se cumple cuota/cobertura de nueve clases ni test por participante. VideoLSP10 contiene frases que no equivalen automáticamente a glosas aisladas. Las muestras escasas/cortas requieren etiquetado y estrategia temporal revisados; DAT-DEBT-01 permanece. MOD-01/MOD-02 pueden recibir implementación y dry-run independientes del corpus por autorización de prototipo, pero entrenamiento/VAL-03 siguen pendientes.
