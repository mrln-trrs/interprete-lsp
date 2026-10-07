# Contratos de backend y persistencia

Fecha: 2026-10-06. Estado: especificación propuesta. Backend existente Python/Flask; no se instala Zod ni otro runtime para esta planificación.

## Contrato observado

`GET /` entrega HTML. `POST /process_frame` acepta `{ "frame": "data:image/jpeg;base64,..." }` y devuelve `{ "frame": "...", "manos": [...], "keypoints": [...] }`. Error de imagen: 400; excepciones: 500 con texto interno. Los keypoints son crudos. No existe endpoint de predicción, almacenamiento o sesión.

## Contrato v1 propuesto

Rutas futuras: `POST /api/v1/sessions` inicia sesión autorizada; `DELETE /api/v1/sessions/{id}` libera recursos; `POST /api/v1/process-frame` procesa un frame. Inferencia se añade al mismo flujo tras M3/M4; no crear un segundo endpoint sin necesidad. Mantener legacy durante migración del cliente, con fecha de retiro registrada en ADR-06.

Petición estricta, rechazo de campos desconocidos:

```json
{
  "session_id": "opaque-id",
  "frame_id": 1,
  "captured_at_ms": 1000.0,
  "frame": "data:image/jpeg;base64,..."
}
```

`session_id`: opaco, emitido por servidor, ligado a autorización, no identifica persona. `frame_id`: entero ≥0 estrictamente creciente en sesión. `captured_at_ms`: número finito monotónico relativo al inicio de sesión, no reloj de pared; gaps y duplicados invalidan la ventana. `frame`: JPEG/base64 estricto, cuerpo ≤1 MiB, imagen decodificada ≤1280×720. Solo `application/json`; sin coerción, booleans no se aceptan como enteros. No tomar timestamps cliente como evidencia confiable para auditoría.

Respuesta de éxito `application/json`:

```json
{
  "success": true,
  "data": {
    "frame_id": 1,
    "frame": "data:image/jpeg;base64,...",
    "hands": [],
    "keypoints": [0.0],
    "feature_schema": "hands-126-v1",
    "normalized": false,
    "prediction": null,
    "processing_ms": 12.0
  },
  "error": null,
  "request_id": "opaque-request-id"
}
```

El array abreviado `[0.0]` ilustra el campo: el contrato real exige exactamente 126 floats finitos. Cada mano tiene `side: Left|Right` y `confidence` finita entre 0 y 1. `prediction` es null sin modelo/ventana válida; con modelo contiene clase permitida, confianza, decisiones estables, estado `candidate|accepted|rejected`, versión y glosa opcional. Nunca confundir confianza de lateralidad con probabilidad de glosa. `normalized` explicita transformación; no normalizar dos veces.

## Errores y semántica HTTP

El envelope propio puede expresar `{success:false,data:null,error:{code,message},request_id}` para compatibilidad. En v1 se elige éxito con envelope y errores estándar Problem Details sin envelope, con status HTTP real. No etiquetar un objeto Problem Details anidado como `application/problem+json`.

```json
{
  "type": "about:blank",
  "title": "Solicitud inválida",
  "status": 400,
  "detail": "El frame no contiene un JPEG válido.",
  "instance": "/api/v1/process-frame",
  "code": "INVALID_FRAME",
  "request_id": "opaque-request-id"
}
```

| HTTP | Condición |
|---|---|
| 400 | JSON/base64/frame inválido, campos extra o timestamp inválido |
| 401 / 403 | Sesión no autorizada / acceso u origen denegado |
| 409 | Frame duplicado o fuera de orden |
| 413 | Cuerpo o dimensiones excedidos |
| 415 | Media type no admitido |
| 429 | Cuota agotada; Retry-After |
| 500 | Fallo inesperado, sin detalle interno |
| 503 | Detector/modelo requerido indisponible o capacidad agotada |

No usar 200 para fallos de validación. Predicción incierta es resultado normal con `rejected`, no error HTTP. `Cache-Control: no-store` en frames y sesión. POST no se reintenta ciegamente: frame_id permite detectar duplicados, el cliente descarta frames caducados. Sesión expira tras cinco minutos de inactividad; una sesión activa inicial, dos solo tras pruebas de aislamiento.

## Validación y tipos

En Python definir DTO tipados y validadores de borde con biblioteca evaluada en M0 o funciones explícitas; exigir claves, tipos, finitud, tamaños y allowlists. Un `TypedDict` por sí solo no valida en runtime. Si posteriormente hay TypeScript, derivar Zod desde el mismo esquema versionado y probar equivalencia; la validación servidor sigue siendo obligatoria.

Tipos internos: `FrameFeatures(frame_id, captured_at_ms, vector: float32[126], schema_version, normalized)`; `Prediction(class_id, confidence, model_version, frame_id)`; `ValidatedGloss(gloss, accepted_at_ms, evidence_frames)`; `Translation(text, glossary_version, source_glosses)`. Nunca pasar consultas Prolog, rutas de archivo o comandos arbitrarios desde entrada HTTP.

## Persistencia y transacciones

MVP: secuencias `.npy` y manifiesto JSON fuera de Git; glosario versionado en configuración; logs mínimos. Grabación: validar → escribir archivo temporal en carpeta destino → verificar forma/hash → renombrar atómicamente → actualizar manifiesto de forma atómica. Recuperación detecta huérfanos y entradas incompletas; no usar una matriz sin registro válido.

Modelo relacional futuro si se justifica SQLite: `gloss(id, code UNIQUE, description)`, `participant(id pseudonymous)`, `consent(id, participant_id FK, version, status)`, `capture_session(id, participant_id FK, consent_id FK, schema_version)`, `sample(id, session_id FK, gloss_id FK, path UNIQUE, checksum, captured_at)`, `model_version(id, schema_version, artifact_hash)`, `audit_event(id, event_type, occurred_at, request_id, model_version_id FK NULL)`. Atributos dependen de su clave; no duplicar descripciones o listas de glosas en una celda. Consentimiento identificable se almacena separadamente y restringido. No persistir video ni predicciones por frame por defecto.

Referencias: [semántica HTTP RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html); [Problem Details RFC 9457, sustituto de 7807](https://www.rfc-editor.org/rfc/rfc9457.html).
