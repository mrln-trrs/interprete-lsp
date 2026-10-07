# API-01 — Contrato v1 y validación estricta

Inicio: 2026-10-06; base `02f4fb4`. Dependencia PLN-01 cumplida; no requiere modelo entrenado. Estado: Done para contrato/validación y conexión al procesador.

Alcance: DTO inmutable FrameRequest, claves exactas, rechazo de duplicados JSON/NaN/booleans como enteros, media type, base64 estricto y JPEG SOF antes del decoder nativo. Límite de cuerpo 1 MiB y dimensiones 1280×720. `/api/v1/process-frame` devuelve envelope en éxito y Problem Details en error; no-store, resultados finitos 126D, confianza de manos en [0,1], prediction null y normalized false. Errores internos genéricos; logs sin imágenes ni detalles de excepción.

El procesador real se conecta en web_server.py mediante callback; v1 falla cerrado 503 mientras SEC-10 no configure sesiones autorizadas. El endpoint legacy no cambia en este commit; la migración del cliente y protección de ambas rutas corresponde a SEC-10.

Validación: seis tests automatizados PASS de éxito, rechazo previo al procesador, límites, JSON duplicado, errores seguros y servicio no configurado. Los tests usan un procesador inyectado y fixture de cabecera; no acreditan decodificación/inferencia real ni performance. Visión tiene sus cuatro tests independientes aprobados en ENV-03.

Límite: sin sesiones, cuotas, predicciones, base de datos o aprobación de exposición remota. Esas dependencias no se consideran completadas por aprobar el contrato. SEC-10 es la siguiente tarea.
