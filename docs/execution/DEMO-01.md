# DEMO-01 — Saludo básico y TTS local

Inicio: 2026-10-06; base `c7aeff8`. Solicitud: agitar una mano, escribir Hola y reproducir TTS.

Alcance: modelo geométrico experimental versionado en `models/gestures/wave_hola.json`, activación explícita `--gesture-demo`. Detecta al menos tres dedos extendidos, desplazamiento horizontal suficiente y dos cambios de dirección; mantiene el evento para pasar la estabilidad de diez frames del pipeline y emite una sola traducción inmediata. Bajar/cerrar la mano durante al menos 900 ms rearma otro saludo. Usa coordenadas crudas antes de eliminar la traslación; cada sesión posee su propio estado. No reemplaza el modo neuronal.

UI: instrucciones, indicador de regla sin porcentaje de precisión y voz habilitada inicialmente en este modo. Botón Probar voz: Hola; el inicio de cámara activa la voz desde una acción del usuario. Prefiere voz local española, con alternativa local del sistema y aviso de pronunciación si no hay español. Nunca requiere audio remoto ni micrófono.

Dependencias: API-01, SEC-10, INF-01, LOG-01, NLP-01, UX-01 y AUD-01. Límite: no es un modelo neuronal entrenado ni validación del saludo oficial LSP. Sus umbrales son heurísticos, no precisión medida; iluminación, cámara y orientación afectan detección. Validación física de gesto y reproducción de audio corresponde a la prueba local del usuario; no se atribuye aceptación de navegador no ejecutada.

Validación: seis pruebas nuevas de onda, deduplicación/rearme, cambio de slot, mano cerrada/quieta/ruido/barrido único, gaps y entrada inválida. JavaScript compila en V8. La suite completa y el reinicio local se registran al cerrar esta tarea.

Resultado de suite: 49 tests, 48 PASS y 1 SKIP (Keras nativo restringido en este Windows), duración interna 6.750 s. El modo geométrico no utiliza Keras. Escaneo de secretos de los módulos de inferencia y del modelo geométrico sin hallazgos. Aceptación física de cámara y TTS pendiente de la prueba del usuario.

Demo reiniciada en `127.0.0.1:5000` con `--gesture-demo`: GET 200, modo gestual y checkbox de voz activos. Smoke real API JPEG vacío → MediaPipe → regla devuelve REPOSO, modelo disponible y texto vacío; sesión de prueba cerrada con 204. Servidor local permanece activo para probar. Estado: Done para implementación y verificación de software acotadas; no aceptación lingüística ni auditiva.

Uso: `python web_server.py --host 127.0.0.1 --port 5000 --gesture-demo`, con LSP_ACCESS_KEY configurada. Abre la cámara, presenta palma abierta hacia ella y agita de lado a lado dos o tres veces durante unos dos segundos. La voz depende de las voces locales disponibles y permisos del navegador; el texto siempre se conserva.
