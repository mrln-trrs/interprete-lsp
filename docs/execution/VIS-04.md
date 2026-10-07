# VIS-04 — Ingeniería de features provisionales

Inicio: 2026-10-06; base `8f77e41`. Estado: Done para esquema exploratorio y validación automatizada; aceptación lingüística/física pendiente como deuda.

El usuario difirió asesor y Arduino y autorizó fuentes gratuitas. Se adopta provisionalmente `hands-126-v1`, bloques Left/Right sobre imagen tipo selfie, normalización `wrist-palm-v1`. No se congela como representación suficiente de LSP. Se agregan validación de rango/forma/finitud y re-muestreo de ventanas de un segundo a 30 puntos, con rechazo de huecos >200 ms, cobertura incompleta y timestamps repetidos. Capturador e inferencia deben consumir la misma función y versión.

Validación: cuatro casos nuevos deterministas de invarianza (tolerancia 1e-5), degeneración, ausencia unilateral, entradas inválidas, duración a 12/30 FPS y gaps; los cuatro tests de visión existentes pasan. La imagen sintética prueba software, no lateralidad física de cámaras ni movimientos semánticos. ENV-03 solo bloquea smoke ML/SSL, no las funciones NumPy verificadas.

Alcance límite: no medir 30 FPS reales o p95 en webcam/red, no afirmar robustez universal ni ablación lingüística. LSP-DEBT-01 y VIS-DEBT-01 documentan pruebas con asesor/corpus futuro. DAT-01 y MOD-01 pueden desarrollarse contra el esquema provisional por autorización explícita; VAL-01 final queda pendiente de cámara/benchmark.
