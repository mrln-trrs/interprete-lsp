# Matriz de trazabilidad

Fecha: 2026-10-06. Cada fila tiene requisito, entrega y caso principal identificable; las pruebas complementarias no rompen esa correspondencia. La tabla siguiente conserva la línea base previa a implementación; la ejecución actual figura después.

| Requisito | Prompt | Especificación / implementación prevista | Caso principal | Evidencia actual |
|---|---|---|---|---|
| VAL-01 | 1, 4 | Visión y normalización | T-VIS-01 | Código y tests presentes; no aceptación |
| VAL-02 | 7 | Dataset y manifiesto | T-DAT-01 | Stubs |
| VAL-03 | 8, 9 | Red, reglas y PLN | T-ML-01 | Stubs; sin modelo verificado |
| VAL-04 | 5, 6, 10 | Tokens, UX, voz/serial | T-UX-01 | UI demo y firmware básico |
| VAL-05 | 2, 3, 11 | Seguridad, contratos y release | T-SEC-01 | Exclusiones; auditoría pendiente |
| SEC-01 | 2 | Sesión/origen autorizado | T-API-01 | Sin control observado |
| SEC-02 | 2, 3 | Límites y esquema estricto | T-API-01 | Validación insuficiente |
| SEC-03 | 2 | Eventos sanitizados y correlación | T-SEC-02 | Pendiente |
| SEC-04 | 2 | HTTPS, errores y secretos | T-SEC-01 | Túnel histórico; scan pendiente |
| SEC-05 | 2 | Cuotas, cola y memoria | T-SEC-02 | Pendiente |
| SEC-06 | 2, 9, 10 | Allowlist y menor privilegio | T-NLP-01 | Integración pendiente |
| SEC-07 | 2, 4 | Aislamiento del tracking | T-SEC-02 | Detector global actual |
| SEC-08 | 2, 7 | Consentimiento y retención | T-DAT-02 | Política propuesta |

Para cerrar una fila agregar ID de ejecución y ruta/hash del reporte, revisor, fecha y resultado. Kanban Done exige implementación más evidencia; documentación creada se marca documentada sin convertir automáticamente el requisito en cumplido. Casos de apoyo: T-VIS-02, T-DAT-02, T-ML-02, T-NLP-01/02, T-UX-02, T-HW-01, T-SYS-01 y T-PERF-01.

## Ejecución actual — 2026-10-06

Evidencia común: [CI Linux](https://github.com/mrln-trrs/interprete-lsp/actions/runs/37558676708), candidato `e4880b7`, 43 tests PASS. Casos sintéticos prueban controles de software; no validan reconocimiento lingüístico.

| Requisito | Evidencia actual | Aceptación global |
|---|---|---|
| VAL-01 | Visión real sin cámara, normalización y ventanas probadas | Cámara/lateralidad/ablación pendientes |
| VAL-02 | Captura atómica, loader y split por persona probados | Corpus/cuotas reales pendientes |
| VAL-03 | LSTM/GRU nativo, reglas, plantillas y pipeline probados | Entrenamiento, precisión y asesor pendientes |
| VAL-04 | Tokens/contraste, siete estados y voz local implementados | Browser/CLS/voz pendientes; Arduino excluido |
| VAL-05 | Contrato/sesiones y scans; dictamen trazado | NO APTO: protobuf alto y gates pendientes |
| SEC-01/02/03/05/07 | API y sesiones: autorización/origen, DTO, errores, cuotas, aislamiento | PASS en alcance automatizado local; despliegue pendiente |
| SEC-04 | Secrets sin coincidencias; no exposición remota nueva | TLS/despliegue y SCA sin altas pendientes |
| SEC-06 | Clases/plantillas acotadas; rechazo y no modelo explícitos | Prolog real pendiente; Arduino excluido |
| SEC-08 | Política y fuentes autorizadas, sin datos personales nuevos | Consentimientos/corpus futuros requieren comprobación |

Revisor técnico: Codex. Registros por tarea en `docs/execution`; alcance y límites quedan vinculados a cada commit. Ninguna fila VAL se cierra por tests sintéticos.
