# Plan de pruebas y evidencia

Fecha: 2026-10-06. Estado: diseñado, ejecución pendiente.

Objetos: visión, contratos/API, corpus/splits, modelo, reglas/PLN, UI y serial. Niveles: unidad en funciones deterministas, integración para fronteras, sistema para pipeline y aceptación con usuarios/asesor LSP. Fixtures sintéticos sin datos personales en Git; corpus/modelos reales en almacén autorizado. No usar un test que solo replique la implementación como evidencia de calidad.

| Caso | Cobertura | Técnica y resultado esperado |
|---|---|---|
| T-VIS-01 | VAL-01 | Ausencia, una/dos manos, orden/lateralidad validada |
| T-VIS-02 | VAL-01 | Traslación/escala y degeneración; finitud/forma/tolerancia |
| T-DAT-01 | VAL-02 | Cancelación/guardado atómico, corrupción, hash y esquema |
| T-DAT-02 | VAL-02 | Grupos de personas disjuntos, cobertura de clases y manifiesto |
| T-ML-01 | VAL-03 | Evaluación test reservado con todas las métricas y soportes |
| T-ML-02 | VAL-03 | Round-trip, incompatibilidad y latencia de inferencia |
| T-NLP-01 | VAL-03 | BVA confianza/estabilidad, pausas, deduplicación y timeout |
| T-NLP-02 | VAL-03 | Plantillas revisadas, glosa desconocida y REPOSO |
| T-UX-01 | VAL-04 | Siete estados, teclado, foco, lector de pantalla y CLS |
| T-UX-02 | VAL-04 | Contraste, zoom/móvil, permisos y hardware opcional |
| T-API-01 | VAL-05 | Tipos/tamaños/errores, sesión/origen y caché |
| T-SEC-01 | VAL-05 | Secret scan árbol/historial + SCA/SBOM fechados |
| T-SEC-02 | VAL-05 | Cuotas, payload excesivo, aislamiento y recuperación |
| T-HW-01 | VAL-04 | Casos HW-T01 a HW-T07 con simulador y placa |
| T-SYS-01 | VAL-03/04 | Pipeline con rechazo, reposo, desconexiones y limpieza |
| T-PERF-01 | VAL-01/04 | Cinco minutos, hardware/red documentados, p50/p95 |

Casos negativos/bordes obligatorios: NaN/Inf, dimension incorrecta, etiqueta ajena, escala cero, umbral 0.8499/0.85/0.8501, estabilidad 9/10/11, timestamp duplicado/gap, payload límite±1 y serial límite±1. Medir falsas emisiones por minuto en reposo y gestos desconocidos; no inferir reconocimiento desde FPS o tests geométricos.

Formato de evidencia: ID de ejecución, caso, commit, esquema/artefactos hash, fecha, herramienta/versión, entorno, precondiciones, pasos, esperado, obtenido, estado PASS/FAIL/BLOCKED/NOT_RUN, defecto y ruta de evidencia sanitizada. Separar resultados de entrenamiento de pruebas de software. No subir video/datos identificables en reportes.

Entrada de M6: entorno reproducible, hitos incluidos terminados, fixtures y responsables definidos. Salida: todos los VAL aplicables PASS, sin defectos críticos ni vulnerabilidades altas/críticas abiertas, riesgos residuales documentados y revisión. Cualquier función excluida (voz/Arduino) debe estar deshabilitada y expresamente fuera del release; no aprobar pruebas pendientes como PASS.

Comando actual existente: `python -m unittest discover tests/` en entorno con dependencias instaladas. Solo hay cuatro tests de visión; su existencia no valida seguridad, clasificador o UI. Esta actualización documental no instala dependencias, entrena modelos ni ejecuta hardware.
