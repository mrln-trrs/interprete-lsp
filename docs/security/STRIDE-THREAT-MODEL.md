# Modelo STRIDE y Secure SDLC

Fecha: 2026-10-06. Estado: análisis estático inicial; controles propuestos, sin auditoría aprobada.

## Activos y fronteras

Activos: video identificable, keypoints derivados sensibles, consentimiento, etiquetas, modelos, tokens de túnel, estación del operador y puerto serial. Fronteras: navegador → red/túnel → Flask → decodificador nativo/detector → archivos locales → modelo/reglas → serial/Arduino. Cámara local solo para escritorio/captura; la demo web recibe imágenes del cliente. No asumir que los keypoints son anónimos por eliminar píxeles.

## Amenazas

| ID / STRIDE | Amenaza concreta | Control requerido | Prueba |
|---|---|---|---|
| SEC-01 / Spoofing | Cliente ajeno consume procesamiento público | Sesión autorizada, expiración y validación de origen; túnel restringido | Sesión inválida 401/403, origen ajeno rechazado |
| SEC-02 / Tampering | JPEG/base64 malformado, payload o modelo manipulado | Esquema cerrado, límites, decoder seguro y hashes de artefactos | Campos extra, NaN, imagen corrupta y checksum inválido |
| SEC-03 / Repudiation | Sin trazabilidad de versión/resultado | Log de evento con request_id, versión, fecha y resultado | Correlación sin imagen, keypoints ni identidad directa |
| SEC-04 / Information disclosure | Video en tránsito/log, excepción interna o token Git | HTTPS, retención nula por defecto, errores públicos genéricos y secret scan | Logs sin payload, respuesta sin traceback, revisión historial |
| SEC-05 / Denial of service | JPEG enorme, cola infinita, clientes concurrentes | Límite 1 MiB de cuerpo, ≤1280×720 decodificado, cuotas y cola acotada | 413/429/503, cancelación y memoria estable |
| SEC-06 / Elevation of privilege | Entrada usada como ruta, consulta Prolog o comando serial | Vocabulario allowlist, rutas resueltas, reglas parametrizadas y comandos cerrados | Traversal, inyección y comandos fuera de rango |
| SEC-07 / Tampering | Estado de tracking compartido altera resultados entre sesiones | Detector y buffers aislados o inferencia estática | Dos clientes no contaminan lateralidad/historial |
| SEC-08 / Disclosure | Dataset compartido públicamente sin consentimiento | Almacenamiento privado, acceso limitado y plazo de eliminación | Acceso/revocación y borrado de derivados verificables |

Los límites son decisiones iniciales del proyecto; validar impacto en la calidad de imagen y hardware. No exponer públicamente hasta probar SEC-01 a SEC-07. Rate limit inicial: 15 solicitudes/s por sesión, máximo dos sesiones autorizadas tras aislamiento; retorno 429 con Retry-After. Un cuerpo JSON base64 crece respecto al JPEG: limitar antes y después de decodificar. Rechazar dimensiones excesivas antes de reservar buffers grandes cuando el decoder lo permita.

## Brechas observadas

`web_server.py` usa `request.get_json(force=True)`, base64 sin validación estricta, `error: str(e)` y servidor de desarrollo Flask en `0.0.0.0`. No se observan autenticación, límites explícitos ni aislamiento por sesión. El lock global solo serializa acceso. `.env.example` es plantilla: el programa no carga automáticamente esas variables. No se verificó el historial completo para secretos ni la seguridad de dependencias; las versiones fijadas no prueban ausencia de vulnerabilidades.

## Checklist de desarrollo seguro

- [ ] Inventario de activos, responsables y uso consentido revisados.
- [ ] Escáner de secretos sobre árbol e historial alcanzable, sin imprimir valores; registrar herramienta/versión/refs/fecha. Si encuentra secreto, rotarlo; ignorarlo no lo elimina del historial.
- [ ] SCA del entorno resuelto con dependencias transitivas, SBOM y reporte fechado; cero altas/críticas abiertas en el alcance del release.
- [ ] Dependencias reproducibles, procedencia de modelos, hash y carga NumPy `allow_pickle=False`.
- [ ] Entradas validadas antes de OpenCV, Prolog y serial; pruebas de abuso.
- [ ] CORS/origen cerrado; permisos de cámara explicados; HTTPS para cámara remota.
- [ ] Proceso sin privilegios administrativos; acceso solo al puerto serial elegido; sin shell dinámico.
- [ ] Logging mínimo y limpieza de sesiones/buffers al detener o expirar.
- [ ] Consentimiento, acceso, revocación y eliminación de dataset definidos antes de recolectar.
- [ ] Revisión independiente y gates de demo local/demo remota/release separados.

Mapeo orientativo a ISO/IEC 27001:2022 Anexo A.8: configuración, control de acceso, vulnerabilidades, desarrollo seguro, pruebas y logging. No constituye conformidad ni certificación. Para OWASP API Security, revisar autorización, consumo de recursos y configuración contra la edición vigente durante M1; adjuntar evaluación de aplicabilidad.
