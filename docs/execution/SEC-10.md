# SEC-10 — Sesiones, cuotas y aislamiento

Inicio: 2026-10-06; base `179f972`. Dependencia API-01 cumplida. Estado: Done para controles implementados y pruebas automatizadas; validación remota y release no aprobados.

Alcance: una sesión autorizada, clave del operador de al menos 32 caracteres en entorno, origen exacto allowlist, token aleatorio en memoria, expiración por 300 s de inactividad, límite de 15 frames/s y 30 intentos de sesión/minuto. Lock no bloqueante devuelve 503 en concurrencia sin cola; frame_id/timestamp crecientes y rechazo 409 de duplicados. HTTP 429/503 con Retry-After. Detector en modo estático evita tracking cruzado. Legacy `/process_frame` retirado con 410, cliente migrado a v1 y con permiso de cámara explícito, parada, timeout y cancelación. Tokens nunca se guardan en storage ni se imprimen; logs de acceso Werkzeug deshabilitados porque la ruta DELETE contiene capability token.

Validación: seis pruebas de sesiones PASS (autorización/origen, capacidad/expiración/orden, cuotas, borrado, busy sin cola y configuración ausente); seis de contrato API siguen PASS. Procesador sustituido en esos tests: no acreditan rendimiento o TLS remoto. Cámara cliente no se transmite sin sesión autorizada. Ya no se conserva la ruta antigua sin proteger.

Configuración local: establecer `LSP_ACCESS_KEY` en el entorno del proceso, iniciar `python web_server.py --host 127.0.0.1`; introducir clave en la interfaz. Para cambiar puerto, orígenes localhost se adaptan al CLI. Remoto exige `LSP_ALLOWED_ORIGINS` explícito (URL HTTPS exacta), TLS y servidor/reverse proxy apropiados; su access log también debe omitir o redactar IDs de sesión. No introducir claves en URL ni en comandos que se publiquen.

Límite: servidor de desarrollo conservado para demo local, no publicar túnel hasta resolver protobuf y auditoría de despliegue. CSP limita recursos externos pero permite inline por la UI existente; extraer scripts y aplicar nonce/hash se registra como deuda UX-SEC-01. Una sesión inicial, sin prometer multiusuario o benchmark. Las revisiones independientes permanecen pendientes.
