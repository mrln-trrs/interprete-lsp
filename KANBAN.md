# Kanban del intérprete LSP

Actualización: **2026-10-06**. Fuente de seguimiento operativo; requisitos en [plan maestro](docs/PLAN-INTERPRETE-LSP.md). Estado basado en inspección del repositorio, sin validar ejecuciones históricas.

## Estados y definición de terminado

**Documentado**: especificación disponible. **Implementado, por verificar**: código presente, aceptación pendiente. **Por hacer**: stub o trabajo no observado. **Bloqueado**: dependencia concreta pendiente. **Done** exige implementación, pruebas pertinentes y evidencia enlazada; crear un archivo no completa la funcionalidad. No se publica un porcentaje global que mezcle documentación con producto funcionando.

## Aplicación de los once prompts

| Fase | Entregable documental | Estado documental | Estado técnico |
|---|---|---|---|
| 1 Planificación | [Plan](docs/PLAN-INTERPRETE-LSP.md), [ADR](docs/architecture/DECISIONS.md) | Documentado | Revisión M0 pendiente |
| 2 Seguridad | [STRIDE](docs/security/STRIDE-THREAT-MODEL.md) | Documentado | Controles y auditoría pendientes |
| 3 Backend | [API](docs/backend/API-CONTRACTS.md) | Documentado | Legacy presente; v1 pendiente |
| 4 Visión | [Visión](docs/vision/VISION-SPEC.md) | Documentado | Implementado, por verificar |
| 5 Diseño | [Tokens](docs/design/DESIGN-TOKENS.md) | Documentado | Aplicación pendiente |
| 6 Ergonomía | [UX](docs/ux/ERGONOMICS-SPEC.md) | Documentado | Demo presente; aceptación pendiente |
| 7 Dataset | [Datos](docs/data/DATASET-PLAN.md) | Documentado | Captura/loader stubs |
| 8 Red | [ML](docs/ml/TRAINING-PLAN.md) | Documentado | Arquitectura/train stubs |
| 9 Lógica/PLN | [Reglas y editorial](docs/nlp/LOGIC-TRANSLATION-SPEC.md) | Documentado | Traductor stub; Prolog ausente |
| 10 Hardware | [Serial](docs/hardware/SERIAL-PROTOCOL.md) | Documentado | Host stub; firmware mínimo |
| 11 Calidad | [Pruebas](docs/quality/TEST-PLAN.md), [auditoría](docs/quality/ISO-25010-AUDIT-REPORT.md) | Documentado | Gate de release no aprobado |

## Inventario de tareas históricas

Se preservan los IDs originales para trazabilidad. Las atribuciones históricas de implementación a Marlon Torres no implican asignación de todo el nuevo backlog.

| ID | Resultado observado | Estado actualizado |
|---|---|---|
| ENV-01 | Python 3.11 declarado; entorno local no acreditado | Por verificar |
| ENV-02 | Estructura y exclusiones presentes | Implementado, por verificar exclusiones futuras |
| VIS-01 | HandDetector, extracción 126D | Implementado, por verificar |
| VIS-02 | Centro muñeca/escala palma | Implementado, por verificar y evaluar pérdida espacial |
| VIS-03 | Visualizador escritorio y salida q/Esc | Implementado, por verificar cámara |
| TST-01 | Cuatro pruebas de visión presentes | Implementado, ejecución pendiente |
| WEB-01 | Flask `/process_frame`, JPEG y lock | Implementado, validación/aislamiento pendientes |
| WEB-02 | UI móvil con cámara cliente | Implementado, aceptación UX pendiente |
| WEB-03 | Instrucciones de ngrok y exclusiones | Despliegue actual y seguridad no verificados |
| DAT-01 | `record_samples.py` solo docstring | Por hacer; se retira el progreso no acreditado |
| DAT-02 | `dataset_loader.py` solo docstring | Por hacer |
| DAT-03 | Dataset no acreditado | Bloqueado por consentimiento, esquema y DAT-01 |
| MOD-01 | `model_builder.py` solo docstring | Por hacer |
| MOD-02 | `train.py` solo docstring | Bloqueado por corpus y MOD-01 |
| NLP-01 | `translator.py` solo docstring | Por hacer |
| HW-01 | Host stub, firmware lee líneas | Por hacer |

## Backlog ejecutable y dependencias

Prioridad P0 antes de exposición o datos reales; P1 para MVP; P2 salidas opcionales. Responsables por rol propuestos, nombres por asignar en M0. Ninguna tarea se marca en progreso sin evidencia.

| ID | Prioridad / hito | Trabajo y aceptación | Depende de | Rol |
|---|---|---|---|---|
| PLN-01 | P0 / M0 | Revisar alcance, VAL, ADR y asignaciones; registro de revisión | Plan documentado | Líder + equipo |
| ENV-03 | P0 / M0 | Entorno limpio/lock, inventario y compatibilidad registrados | PLN-01 | DevSecOps |
| SEC-09 | P0 / M1 | Ejecutar secret scan e historial + SCA/SBOM sanitizados | ENV-03 | Seguridad |
| API-01 | P0 / M1 | DTO/validación estricta, límites y errores según contrato | PLN-01 | Backend |
| SEC-10 | P0 / M1 | Sesión/origen, cuotas, errores seguros y aislamiento | API-01 | Seguridad + backend |
| VIS-04 | P0 / M1 | Lateralidad, features/ablación y tiempos; congelar esquema | ENV-03 | Visión + asesor LSP |
| DAT-04 | P0 / M2 | Consentimiento, acceso/retención y participantes | PLN-01 | Datos |
| DAT-01 | P1 / M2 | Captura con cuenta regresiva, timestamps y guardado atómico; T-DAT-01 | VIS-04, DAT-04 | Datos |
| DAT-02 | P1 / M2 | Loader seguro, manifiesto y split por persona; T-DAT-02 | DAT-01 | Datos |
| DAT-03 | P1 / M2 | 30–50 secuencias/clase, nueve clases, cobertura de splits | DAT-02 | Datos + asesor LSP |
| MOD-01 | P1 / M3 | Baseline LSTM/GRU compilado, comparación registrada | Esquema VIS-04 | ML |
| MOD-02 | P1 / M3 | Entrenamiento, métricas y artefactos; VAL-03 | DAT-03, MOD-01 | ML |
| INF-01 | P1 / M4 | Ventana temporal y rechazo de gaps/modelos incompatibles | MOD-02 | ML + visión |
| LOG-01 | P1 / M4 | Spike Prolog, reglas, deduplicación y BVA; T-NLP-01 | INF-01 | Lógica |
| NLP-01 | P1 / M4 | Plantillas de español revisadas, sin inventar frases; T-NLP-02 | LOG-01 | PLN + asesor LSP |
| DS-01 | P1 / M5 | Aplicar tokens, medir contraste y CLS | PLN-01 | UI |
| UX-01 | P1 / M5 | Siete estados, preflight, foco/teclado y recuperación | DS-01, INF-01 | UI + QA |
| AUD-01 | P2 / M5 | Voz opcional, cola acotada y fallo conserva texto | NLP-01 | Integración |
| HW-01 | P2 / M5 | Host y firmware con ACK, límites y desconexión; HW-T01–07 | Protocolo y placa elegida | Hardware |
| QA-01 | P1 / M6 | Integración, sistema, accesibilidad y benchmark con evidencia | Hitos incluidos M1–M5 | QA |
| REL-01 | P0 / M6 | VAL trazados, SCA vigente y dictamen APTO/NO APTO | QA-01, SEC-09/10 | QA + líder |

## Orden de ejecución y gates

### Ejecución autorizada el 2026-10-06

| Tarea | Estado | Registro |
|---|---|---|
| PLN-01 | Done (revisión técnica y autorización de implementación) | [Inicio, alcance y límites](docs/execution/PLN-01.md) |
| ENV-03 | Parcial / bloqueado: DLL SSL y optree por política Windows | [Entorno, pruebas y límites](docs/execution/ENV-03.md) |
| SEC-09 | Done como auditoría; hallazgo alto abierto bloquea release | [Alcance y evidencia](docs/execution/SEC-09.md) |
| API-01 | Done: contrato v1, validación y conexión; acceso cerrado hasta SEC-10 | [Contrato y seis pruebas](docs/execution/API-01.md) |
| SEC-10 | Done: sesiones/cuotas/aislamiento; demo remota aún no aprobada | [Controles, pruebas y límites](docs/execution/SEC-10.md) |
| VIS-04 | Done para prototipo; asesor/ablación/cámara quedan como deuda | [Esquema provisional y pruebas](docs/execution/VIS-04.md) |
| DAT-04 | Done para política y fuentes abiertas; nuevas grabaciones requieren consentimiento | [Gobierno y límites](docs/execution/DAT-04.md) |
| DAT-01 | Done: capturador/persistencia; sin abrir cámara o recolectar corpus | [Inicio y tres pruebas](docs/execution/DAT-01.md) |
| DAT-02 | Done: loader seguro y split por persona; corpus real pendiente | [Inicio y tres pruebas](docs/execution/DAT-02.md) |
| DAT-03 | Parcial: corpus abierto inspeccionado, cobertura/cuotas insuficientes | [Conteos y límites](docs/execution/DAT-03.md) |
| MOD-01 | Parcial: baseline implementado; ejecución Keras bloqueada por ENV-03 | [Configuración y límites](docs/execution/MOD-01.md) |
| MOD-02 | Parcial: pipeline/dry-run y métricas implementados; sin entrenar | [Validación y gates](docs/execution/MOD-02.md) |
| INF-01 | Done para motor aislado; modelo real pendiente MOD-02 | [Inicio y tres pruebas](docs/execution/INF-01.md) |
| LOG-01 | Parcial: reglas Python probadas; paridad/runtime Prolog pendiente | [Reglas y límites](docs/execution/LOG-01.md) |
| NLP-01 | Done para plantillas exploratorias y pipeline; asesor/modelo real pendientes | [Inicio y pruebas](docs/execution/NLP-01.md) |
| DS-01 | Parcial: tokens/layout y contraste ≥7:1; CLS/browser pendiente | [Cambios y medición](docs/execution/DS-01.md) |

El usuario autorizó implementar siguiendo el plan. Codex asume trabajo técnico; validación lingüística, consentimiento y hardware real conservan responsables externos pendientes. El gate de release no cambia.

M0 revisión → M1 visión/seguridad → M2 corpus → M3 modelo → M4 reglas/PLN → M5 integración → M6 auditoría. Diseño UX y simulación serial pueden prepararse después de M0 sin esperar entrenamiento. La demo remota requiere controles P0 y pruebas específicas antes de exposición; el MVP requiere todos los VAL aplicables.

WIP máximo dos tareas por equipo. Registrar en cada tarea propietario, rama, inicio, evidencia, revisión y cierre. Fechas de sprint se fijan tras conocer disponibilidad de equipo/participantes; estimaciones en el plan son esfuerzo, no compromisos de calendario.

[Matriz de trazabilidad](docs/quality/TRACEABILITY-MATRIX.md) y [gate de release](docs/quality/ISO-25010-AUDIT-REPORT.md) mantienen los resultados técnicos pendientes. La solicitud actual completa planeación; no implementa stubs ni aprueba una liberación.
