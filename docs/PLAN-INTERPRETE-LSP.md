# Plan maestro del intérprete LSP

Actualización: 2026-10-06. Versión documental: 1.0. Estado: planificación formalizada; validación técnica y revisión del equipo pendientes.

## Visión, problema y resultado esperado

El prototipo académico busca reconocer un vocabulario cerrado de Lengua de Señas Peruana mediante cámara, expresar glosas validadas como texto en español y ofrecer voz y visualización Arduino opcionales. La demo actual detecta manos; todavía no interpreta señas. La utilidad y corrección lingüística deben validarse con personas usuarias de LSP y un asesor lingüístico antes de afirmar capacidad de traducción.

Usuarios: persona señante, operador de demostración, recolector de muestras y evaluador. Resultado del MVP: captura consentida, entrenamiento reproducible y reconocimiento de nueve clases con rechazo de incertidumbre. No sustituye a un intérprete profesional ni se destina a decisiones médicas, legales o de emergencia.

## Inventario comprobado

Inspección estática del repositorio realizada el 2026-10-06; las afirmaciones históricas del Kanban y artículo no equivalen a pruebas ejecutadas en esta revisión.

| Área | Evidencia | Estado real |
|---|---|---|
| Configuración | `config/settings.py`, `config/actions.py` | 30 FPS objetivo, 30 muestras, umbral 0.85, estabilidad 10, nueve clases |
| Visión | `src/vision/mediapipe_detector.py`, `normalization.py`, `src/main.py` | Implementación presente; aceptación pendiente |
| Web | `web_server.py` | Flask, cámara cliente, JPEG/base64, detector global protegido por lock |
| Pruebas | `tests/test_vision.py` | Cuatro casos presentes; ejecución actual pendiente |
| Dataset | `src/dataset/record_samples.py`, `dataset_loader.py` | Solo docstrings; sin funciones de captura/carga |
| Red | `src/training/model_builder.py`, `train.py` | Solo docstrings; sin entrenamiento ni métricas |
| PLN y serial | `src/nlp/translator.py`, `src/hardware/serial_controller.py` | Solo docstrings |
| Arduino | `arduino/lsp_display_controller/lsp_display_controller.ino` | Lectura de línea; sin protocolo ni salida física |
| Prolog, corpus y modelo | Sin `.pl`, dataset o modelo entrenado comprobado | Pendientes; carpetas locales ignoradas no prueban ausencia en otros equipos |
| Seguridad y despliegue | `.gitignore`, `.env.example` | Exclusiones presentes; historial, SCA y despliegue actual no auditados |

## Alcance y KISS/YAGNI

| Dentro del MVP | Fuera del MVP |
|---|---|
| REPOSO, HOLA, GRACIAS, POR_FAVOR, AYUDA, YO, QUERER, AGUA, BUENOS_DIAS | Interpretación general de LSP o cobertura de sus componentes no manuales |
| Reconocimiento LSP → glosas → español por plantillas revisadas | Español → LSP, avatar y traducción bidireccional |
| Escritorio local y demo web controlada | Servicio público permanente, multiusuario a escala, cuentas y facturación |
| Dataset local consentido y partición por participante | Recopilación masiva, reconocimiento de identidad y retención de video por defecto |
| Arduino y voz opcionales, degradación a texto | Actuadores críticos, hardware autónomo certificado |
| Reglas de confianza/estabilidad y prueba de integración Prolog | LLM remoto, generación libre de frases y entrenamiento de grandes modelos |

## Arquitectura y presupuesto temporal

Flujo objetivo: cámara → MediaPipe → vector crudo 126D → normalización versionada → ventana `(30,126)` → red recurrente → reglas → glosas → plantillas → texto/voz/serial. La demo web actual termina en landmarks y vector crudo; no debe alimentar entrenamiento como si ya estuviera normalizada.

Cada mano se centra en su muñeca y se escala respecto al punto 9; el código usa distancia máxima como alternativa si la palma es degenerada. Esa normalización elimina posición global y relación espacial entre manos: evaluar su efecto con asesor LSP y pruebas de ablación antes de congelar el esquema. Las coordenadas z de MediaPipe no son profundidad métrica calibrada. Cámara/espejo y lateralidad deben tener convención idéntica en captura e inferencia.

30 FPS es objetivo de captura, no garantía. A 30 FPS, 30 muestras cubren aproximadamente un segundo; a 12 FPS, aproximadamente 2.5 segundos. Registrar timestamps monotónicos y re-muestrear a 30 instantes sobre una ventana de un segundo; si hay huecos superiores a 200 ms o cobertura insuficiente, devolver Partial sin inferencia. La captura local a 30 FPS es el camino inicial de dataset. La captura web queda condicionada a validación de re-muestreo.

Presupuestos propuestos para aceptación en un equipo de referencia documentado: captura local efectiva ≥25 FPS, procesamiento p95 ≤100 ms, RTT web p95 ≤250 ms con un cliente y cola acotada; no prometer 30 FPS de inferencia ni extender estos valores a internet en general. Registrar CPU, RAM, SO, cámara, resolución, versiones, número de clientes, red y mediciones durante cinco minutos. Una petición pendiente por cliente; descartar frames antiguos antes que acumular latencia. La estabilidad requiere diez decisiones consecutivas de la misma clase ≥0.85, asociadas a frames nuevos; reiniciar ante huecos, clase distinta o confianza baja. Registrar cadencia para medir la demora adicional.

El detector global de la web comparte estado temporal entre clientes aunque tenga lock. Antes de aceptar varias sesiones, aislar detector/buffers por sesión con límite de recursos o usar detección sin tracking temporal. Primero habilitar una única sesión controlada.

## Pila tecnológica y matriz Build vs. Adopt

| Capacidad | Decisión | Justificación / condición |
|---|---|---|
| Visión | Adoptar OpenCV y MediaPipe existentes | Evitar entrenar detector propio; verificar lateralidad y compatibilidad |
| Datos | Adoptar NumPy y scikit-learn; construir manifiesto | `.npy` con carga sin pickle y split por participante |
| Secuencias | Adoptar TensorFlow/Keras; construir baseline LSTM/GRU | Comparar costo/F1; no adoptar Transformer sin evidencia |
| Backend | Conservar Flask | No añadir Node solo para Zod; validación estricta Python en servidor |
| UI | Conservar HTML/CSS/JS de la demo | Tokens semánticos y estados; TypeScript/Zod solo si migración posterior lo justifica |
| Persistencia | Archivos locales y JSON versionado | SQLite 3NF solo al necesitar diccionario editable/auditoría transaccional |
| Lógica | Construir reglas y evaluar puente SWI-Prolog | Prolog no está instalado ni integrado; comparar equivalencia con referencia Python |
| Salida | Adoptar PySerial/pyttsx3 | Opcionales, sin bloquear captura; protocolo acotado |
| Infraestructura | Demo local; túnel controlado condicionado | Sin microservicios, Kubernetes o nube en MVP |

`requirements.txt` fija la mayoría de versiones pero `flask>=3.0` está abierto. El runtime Python 3.11 es la base histórica del proyecto, no una compatibilidad revalidada. Antes de implementar, resolver un entorno limpio y lock reproducible, revisar soporte y vulnerabilidades y registrar cambios; no actualizar dependencias a ciegas.

## Criterios de aceptación principales

Son requisitos futuros, todos pendientes. Los casos detallados y la evidencia se vinculan en [trazabilidad](quality/TRACEABILITY-MATRIX.md).

```gherkin
Feature: MVP académico LSP de vocabulario cerrado
  Scenario: VAL-01 Captura geométrica consistente
    Given una cámara y convención de lateralidad documentadas
    When se procesa una mano, dos manos, ausencia y palma degenerada
    Then se obtiene un vector finito float32 de 126 valores
    And los bloques ausentes son ceros y se conserva el orden izquierda-derecha
    And los casos de traslación y escala satisfacen tolerancia 1e-5

  Scenario: VAL-02 Dataset reproducible y consentido
    Given participantes con consentimiento y manifiesto sin identidad directa
    When se capturan y particionan secuencias de las nueve clases
    Then cada secuencia válida tiene forma 30 por 126 y timestamps verificables
    And ninguna persona aparece en más de una partición
    And existen al menos 30 secuencias válidas por clase

  Scenario: VAL-03 Reconocimiento evaluado y prudente
    Given un modelo y esquema versionados y test reservado por participante
    When se evalúa el test una sola vez tras seleccionar hiperparámetros
    Then se reportan accuracy, precision, recall, macro-F1 y matriz de confusión
    And macro-F1 es al menos 0.85 y recall por clase al menos 0.70
    And ninguna glosa se emite sin confianza 0.85 y diez decisiones estables
    And REPOSO y secuencias ambiguas no producen frases

  Scenario: VAL-04 Interacción estable y degradación
    Given la consola con siete estados y hardware opcional
    When falla cámara, red, modelo, audio o serial
    Then se muestra el estado y una recuperación accesible por teclado
    And se conserva el texto confirmado sin emitir predicciones obsoletas
    And el texto alcanza contraste 7 a 1 y CLS web no supera 0.1

  Scenario: VAL-05 Seguridad y liberación trazable
    Given el candidato identificado por commit y configuración
    When se ejecutan seguridad, pruebas y revisión de calidad
    Then no hay secretos confirmados en archivos ni historial alcanzable auditado
    And no hay vulnerabilidades altas o críticas abiertas en el alcance evaluado
    And cada requisito tiene caso, resultado y evidencia identificables
    And la exposición pública queda bloqueada si falta un control crítico
```

Las metas de F1 son decisiones de proyecto, no resultados ni garantía estadística. Si el corpus no permite test independiente por persona, el entregable se limita a demo exploratoria y VAL-03 permanece pendiente.

## Once fases y entregables

| Prompt | Entregable adaptado | Condición de salida |
|---|---|---|
| 1 Planificación | Este plan y [decisiones](architecture/DECISIONS.md) | Alcance, contratos, criterios y riesgos revisados |
| 2 Seguridad | [STRIDE](security/STRIDE-THREAT-MODEL.md) | Controles críticos implementados y auditados |
| 3 Backend | [Contratos](backend/API-CONTRACTS.md) | Validación Python y compatibilidad verificadas |
| 4 Visión | [Especificación](vision/VISION-SPEC.md) | Normalización y presupuesto medidos |
| 5 Tokens | [Diseño](design/DESIGN-TOKENS.md) | Contraste y herencia revisados |
| 6 Ergonomía | [UX](ux/ERGONOMICS-SPEC.md) | Operación por teclado y recuperación verificadas |
| 7 Datos | [Dataset](data/DATASET-PLAN.md) | Corpus consentido, íntegro y sin fuga entre splits |
| 8 Red | [Entrenamiento](ml/TRAINING-PLAN.md) | Modelo y evaluación reproducibles |
| 9 Prolog/PLN | [Lógica y editorial](nlp/LOGIC-TRANSLATION-SPEC.md) | Reglas equivalentes y frases aprobadas |
| 10 Hardware | [Serial](hardware/SERIAL-PROTOCOL.md) | Simulación, límites y desconexión aprobados |
| 11 Calidad | [Pruebas](quality/TEST-PLAN.md), [auditoría](quality/ISO-25010-AUDIT-REPORT.md) | Evidencia completa y dictamen de liberación |

## Orquestación, hitos y bloqueo pre-código

Esta solicitud entrega documentación; no modifica fuente, dependencias o firmware. El bloqueo pre-código se aplica a nuevos cambios funcionales hasta revisión documentada del plan, sin fingir que el repositorio empieza desde cero. Las skills nombradas en los prompts no están disponibles en esta sesión; sus objetivos se traducen en especificaciones, sin afirmar haber ejecutado esas skills o auditorías.

| Hito | Trabajo y dependencia | Estimación de esfuerzo, sin fechas comprometidas |
|---|---|---|
| M0 | Revisar plan, ADR y responsables; resolver entorno | 2–3 días-persona |
| M1 | Seguridad web, contratos, aislamiento y validación de visión; depende M0 | 4–6 días-persona |
| M2 | Capturador, loader, consentimiento y corpus; depende esquema M1 | 5–8 días-persona más disponibilidad de participantes |
| M3 | LSTM/GRU, selección y evaluación; depende M2 | 3–5 días-persona |
| M4 | Buffer/inferencia, reglas Prolog y PLN; depende M3 | 4–6 días-persona |
| M5 | Tokens/UX, voz y Arduino opcionales; diseño paralelo, integración depende M4 | 3–5 días-persona |
| M6 | Pruebas integrales, SCA y dictamen; depende hitos incluidos | 2–4 días-persona |

Orden y estados operativos: [KANBAN](../KANBAN.md). No se da por iniciado trabajo sin evidencia. WIP máximo: dos tareas por equipo; propietario único por tarea; revisión independiente para controles críticos. Asignaciones y disponibilidad pendientes del equipo; el responsable histórico no se transfiere automáticamente a nuevas tareas.

## Riesgos y decisiones pendientes

| Riesgo | Respuesta | Responsable propuesto |
|---|---|---|
| Señas requieren cara, cuerpo y espacio que manos normalizadas pierden | Validación lingüística y ablación; reducir alcance o versionar features | ML + asesor LSP |
| Corpus pequeño/fuga por persona | Split por participante, test reservado, informe de límites | Datos + QA |
| FPS web diferente de entrenamiento | Timestamps, re-muestreo, rechazo de huecos | Visión |
| Detector global mezcla tracking | Aislamiento o modo estático y límite de sesiones | Backend |
| Demo expuesta recibe datos sin límites | Endurecimiento y gate separado de demo local | Seguridad |
| Prolog añade instalación y latencia | Spike acotado; decisión registrada, nunca omitir reglas | Lógica |
| Placa/LCD/voz no disponibles | Simuladores y texto base; evidencia física pendiente | Hardware |

Pendientes externos: participantes y consentimiento, asesor LSP, equipo de referencia, placa/display exactos y revisión del plan. Las tareas documentales quedan terminadas; los gates técnicos siguen abiertos.

## Referencias normativas y vigilancia

RFC 9457 reemplaza RFC 7807; el contrato distingue envelope propio de Problem Details estándar ([RFC Editor](https://www.rfc-editor.org/rfc/rfc9457.html)). ISO/IEC 25010:2023 define nueve características, por lo que se actualiza el criterio de ocho del prompt ([ISO](https://www.iso.org/standard/78176.html)). WCAG 2.2 ofrece el criterio de contraste mejorado 7:1 para texto normal, con excepciones; el proyecto adopta 7:1 para su texto funcional sin atribuir conformidad AAA global ([W3C](https://www.w3.org/TR/WCAG22/)).

ISO 27001:2022 e ISO 29119 se usan como orientación de seguridad y pruebas; no se ha realizado evaluación cláusula por cláusula ni certificación. Revisar dependencias y fuentes oficiales al inicio de cada hito y antes de liberar; registrar fecha, impacto, alternativa y ADR, preservando KISS/YAGNI.
