# Matriz de trazabilidad

Fecha: 2026-10-06. Cada fila tiene requisito, entrega y caso principal identificable; las pruebas complementarias no rompen esa correspondencia. Estado técnico general NOT_RUN.

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
