# Registro de decisiones de arquitectura

Fecha: 2026-10-06. Decisiones propuestas para revisión en M0; ninguna supone implementación.

| ADR | Decisión | Alternativa y consecuencia | Revisión |
|---|---|---|---|
| ADR-01 | Conservar Python/Flask y módulos actuales | Node/Zod añadirían runtime; validación estricta nativa Python | Al introducir frontend compilado |
| ADR-02 | MVP unidireccional de nueve clases | Traductor general requiere corpus y features adicionales | Con validación de comunidad LSP |
| ADR-03 | Congelar features solo después de ablación | Centrar cada muñeca pierde ubicación relativa; ampliar features invalida corpus/modelo | Antes de recolección definitiva |
| ADR-04 | Ventana de un segundo re-muestreada a 30 instantes | Treinta frames sin timestamps varían de duración | Benchmark de captura |
| ADR-05 | Archivos NumPy/JSON; SQLite condicionado | No crear base/API CRUD sin necesidad concreta | Diccionario editable o auditoría transaccional |
| ADR-06 | API v1 versionada sin romper `/process_frame` silenciosamente | Envelope y Problem Details son contratos distintos | Antes de migrar el cliente |
| ADR-07 | Una sesión web inicial; tracking aislado para concurrencia | Lock global evita carrera pero no mezcla de historial | Pruebas multi-cliente |
| ADR-08 | Reglas obligatorias; spike SWI-Prolog | Añade instalación; referencia Python sirve para equivalencia | Antes de M4 |
| ADR-09 | `.keras` como candidato principal; `.h5` solo compatibilidad | Prompt exige `.h5`; comprobar serialización en entorno fijado | M3, round-trip de modelo |
| ADR-10 | Seguridad, evaluación y calidad con evidencia | Etiquetas ISO no prueban certificación | Cada release |

Todo cambio registra problema, opciones, decisión, responsable, evidencia y efecto sobre VAL, esquema, datos y pruebas. Modificar dimensión, orden de clases o normalización requiere nueva versión de esquema y regeneración controlada de artefactos.
