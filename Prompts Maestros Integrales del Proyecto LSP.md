Prompts Maestros Integrales y Protocolo de Orquestación: Intérprete de Lengua de Señas con IA (LSP)

Este documento recopila la versión avanzada, rigurosa y formal de los prompts utilizados para la planificación, arquitectura, seguridad, desarrollo, pruebas y auditoría de calidad del proyecto **LSP**. Están diseñados bajo un estricto bloqueo pre-código y alineados con las skills maestras (ISO 27001, ISO 29119, ISO 25010, Backend RFC 9110, WCAG 2.2 y Ergonomía de Sistemas).

Kanban Fase 1: Planificación, Estrategia y Vigilancia Tecnológica (Nivel 3 \- Enterprise Suite)

Prompt Maestro 1: Arquitectura, Alcance y Vigilancia Tecnológica (project-planning)

* **Rol:** Director de Planificación y Estrategia de Software / Lead Systems Architect.  
* **Tarea:** Diseñar la arquitectura holística pre-desarrollo, aplicando la matriz Build vs. Adopt, filtrado estricto KISS/YAGNI y delimitación de alcance (*In-Scope* vs. *Out-of-Scope*) para el sistema de visión y traducción LSP.  
* **Contexto:** Se requiere iniciar el proyecto bajo el protocolo de Bloqueo Pre-Código (*Zero-Code Planning Gate*), prohibiendo la modificación de código fuente hasta formalizar el documento maestro en docs/PLAN-INTERPRETE-LSP.md con criterios unívocos de aceptación (VAL-\*).  
* **Restricciones:**  
  * Evaluar la viabilidad de captura continua (30 FPS teóricos frente a restricciones de latencia en hardware estándar).  
  * Definir la taxonomía de la interfaz de usuario bajo armazón estático (shell invariance) para evitar saltos espaciales (CLS).  
  * Integrar la estrategia de modelado de amenazas STRIDE de forma preventiva.  
* **Formato:** Documento Markdown formal estructurado en docs/PLAN-INTERPRETE-LSP.md conteniendo Visión y Problema (PRD Lean), Matriz de Alcance, Pila Tecnológica Justificada y Criterios de Aceptación bajo formato Bherkin/Gherkin (VAL-01 a VAL-05).

Kanban Fase 2: Ciberseguridad, DevSecOps y Modelado de Amenazas (ISO 27001\)

Prompt Maestro 2: Arquitectura de Seguridad y Desarrollo Seguro (iso-27001-secdev)

* **Rol:** Lead Cybersecurity Architect & DevSecOps Engineer.  
* **Tarea:** Diseñar el perímetro de seguridad, controles de acceso y mitigación de vectores de ataque alineados con el Anexo A.8 de la norma ISO/IEC 27001:2022 y OWASP API Security Top 10\.  
* **Contexto:** El sistema maneja flujos de video locales, datos biométricos temporales y comunicación serial con hardware externo, requiriendo un aislamiento estricto de secretos y protección de componentes.  
* **Restricciones:**  
  * Garantizar cero secretos commiteados en el repositorio (.env.example aislado y verificación de historial Git).  
  * Aplicar el principio de menor privilegio (PoLP) en los pipelines de comunicación Python-Arduino.  
  * Diseñar la matriz de mitigación de amenazas STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).  
* **Formato:** Reporte técnico de seguridad en docs/security/STRIDE-THREAT-MODEL.md con checklist de cumplimiento Secure SDLC.

Kanban Fase 3: Modelado de Datos y Contratos de Backend (RFC 9110\)

Prompt Maestro 3: Ingeniería de Backend, Modelado de Datos y Contratos de API (backend-api-architecture)

* **Rol:** Lead Backend Engineer & Data Architect.  
* **Tarea:** Diseñar el modelo de persistencia local/remota, esquemas de validación estrictos (Zod) y contratos de respuesta unificados para el procesamiento de glosas y metadatos del sistema LSP.  
* **Contexto:** Las secuencias de keypoints y traducciones de glosas requieren una estructura transaccional predecible, con tipado estricto y manejo uniforme de errores bajo RFC 7807\.  
* **Restricciones:**  
  * Implementar el Contrato de Respuesta Unificado (API Envelope: success, data, error).  
  * Validar toda entrada de datos en el borde mediante esquemas Zod estrictos.  
  * Garantizar normalización relacional 3NF para la gestión de diccionarios de glosas y logs de auditoría.  
* **Formato:** Especificación técnica de backend en docs/backend/API-CONTRACTS.md conteniendo interfaces tipadas y flujos transaccionales.

Kanban Fase 4: Percepción Visual y Normalización Espacial (MediaPipe)

Prompt Maestro 4: Ingeniería del Subsistema de Visión y Normalización Espacial (ui-layout-spatial-harmony)

* **Rol:** Ingeniero de Machine Learning y Visión por Computador experto en OpenCV, MediaPipe Hands y UI Espacial.  
* **Tarea:** Desarrollar el módulo de detección y normalización de puntos clave (mediapipe\_detector.py y normalization.py) asegurando estabilidad espacial y cero layout shift.  
* **Contexto:** El sistema capta un flujo de video mediante webcam estándar, extrayendo $21$ puntos tridimensionales por mano ($126$ características espaciales normalizadas para configuraciones de dos manos), garantizando robustez ante variaciones de distancia e iluminación.  
* **Restricciones:**  
  * Optimizar el loop de procesamiento para minimizar la latencia de captura.  
  * Implementar rutinas de normalización matemática para centrar las coordenadas respecto a la palma de la mano.  
  * Mantener una interfaz de visualización fluida con canal de scroll y armazón estático (shell invariance).  
* **Formato:** Código fuente tipado en Python (mediapipe\_detector.py y normalization.py) acompañado de un diagrama de flujo de transformaciones geométricas.

Kanban Fase 5: Sistema de Diseño y Herencia de Tokens W3C (Design Systems)

Prompt Maestro 5: Arquitectura de Tokens Visuales y Armonía Cromática (design-system-token-inheritance)

* **Rol:** Design Systems Architect & Visual Synchronization Specialist.  
* **Tarea:** Diseñar el sistema de diseño basado en tokens W3C (DTCG) y la herencia cromática para la interfaz de escritorio e interfaces web del intérprete LSP.  
* **Contexto:** La consola del operador requiere un diseño sobrio, contraste accesible WCAG AAA y sincronización visual impecable entre estados de procesamiento y salida de audio/texto.  
* **Restricciones:**  
  * Definir variables CSS inmutables (--accent, \--surface, \--text-primary) con herencia en cascada.  
  * Asegurar ratios de contraste de color $\geq 7:1$ para accesibilidad visual estricta.  
  * Erradicar saltos visuales y asegurar una jerarquía tipográfica foveal óptima (max-w-prose).  
* **Formato:** Especificación de diseño en docs/design/DESIGN-TOKENS.md con tablas de variables y directrices de herencia.

Kanban Fase 6: Ergonomía de Herramientas y Estado de Flujo (authoring-editor-ergonomics)

Prompt Maestro 6: Ergonomía de Interfaz y Optimización del Estado de Flujo (authoring-editor-ergonomics)

* **Rol:** Flow-State Authoring Specialist & Ergonomics Engineer.  
* **Tarea:** Diseñar la disposición interactiva de la consola de traducción en vivo, implementando una vista dual (*Dual-Pane*), barra de acciones flotante accesible y atajos *Keyboard-First*.  
* **Contexto:** El intérprete es operado en tiempo real; el usuario requiere retroalimentación visual inmediata y un entorno libre de distracciones mecánicas o clics excesivos ($\leq 2$ clics).  
* **Restricciones:**  
  * Implementar barras de control pegajosas (z-30) y gestión limpia de eventos de teclado.  
  * Proveer semáforos preflight preventivos para el estado del puerto serial y la cámara web.  
  * Eliminar el atrapamiento del foco de teclado (Tab trapping).  
* **Formato:** Guía de arquitectura de interacción en docs/ux/ERGONOMICS-SPEC.md con flujos de operador y esquemas de vistas.

Kanban Fase 7: Adquisición de Muestras y Estructuración de Datasets

Prompt Maestro 7: Sistema de Adquisición de Muestras y Estructuración de Datasets (frontend-uxui)

* **Rol:** Lead Data Engineer & Frontend State Architect.  
* **Tarea:** Construir los scripts interactivos de recolección y carga de datos (record\_samples.py y dataset\_loader.py) junto con la matriz de 7 estados mandatorios de la UI.  
* **Contexto:** Se requiere poblar el repositorio local con matrices de características numéricas en directorios normalizados (data/keypoints/\[SEÑA\]/), permitiendo registrar secuencias temporales asociadas a glosas (ej. "HOLA", "GRACIAS", "REPOSO").  
* **Restricciones:**  
  * Estructurar los datos en arrays de numpy (.npy) optimizados para particionamiento *Train/Test Split*.  
  * Implementar la matriz de 7 estados en la UI de captura (*Idle, Loading, Success, Empty, Error, Partial, Offline*).  
  * Asegurar la separación estricta de directorios locales excluidos en el .gitignore.  
* **Formato:** Código fuente modular en Python con instrucciones de ejecución por consola y esquemas de estados interactivos.

Kanban Fase 8: Entrenamiento Neuronal Recurrente (Deep Learning)

Prompt Maestro 8: Arquitectura y Entrenamiento de Redes Secuenciales LSTM/GRU (frontend-uxui)

* **Rol:** Lead Deep Learning Engineer & Recurrent Neural Network Specialist.  
* **Tarea:** Diseñar y ejecutar la arquitectura de clasificación secuencial temporal (model\_builder.py y train.py) para reconocer señas dinámicas de la LSP.  
* **Contexto:** La red neuronal procesa ventanas temporales de $30$ fotogramas consecutivos de keypoints normalizados, mapeando la evolución espacial y temporal del gesto hacia una distribución probabilística de glosas.  
* **Restricciones:**  
  * Utilizar Keras/TensorFlow con capas LSTM o GRU optimizadas contra sobreajuste (*dropout* y regularización).  
  * Registrar métricas de evaluación formales: Accuracy, Precision, Recall, F1-score y Matriz de Confusión.  
  * Exportar el modelo entrenado a models/trained/lstm\_lsp\_model.h5 y el codificador a models/trained/label\_encoder.json.  
* **Formato:** Código fuente completo de la arquitectura y pipeline de entrenamiento, acompañado de tabla de hiperparámetros.

Kanban Fase 9: Inferencia Lógica, PLN y Traducción de Glosas

Prompt Maestro 9: Orquestación Lógica (Prolog) y Procesamiento de Lenguaje Natural (editorial-excellence)

* **Rol:** Lead AI Logic Specialist & Editorial Technical Writer.  
* **Tarea:** Integrar la capa de validación lógica basada en reglas estrictas (Prolog) y el módulo de traducción sintáctica en español (translator.py) bajo estrictas normas ortotipográficas.  
* **Contexto:** Las glosas brutas obtenidas por el modelo neuronal (ej. \[yo, querer, agua\]) deben superar umbrales de confianza ($\geq 0.85$) y estabilidad temporal ($\geq 10$ frames) antes de ser transformadas por el componente de PLN en oraciones fluidas.  
* **Restricciones:**  
  * Definir un motor de reglas en Prolog para rechazar predicciones inestables o ambiguas.  
  * Aplicar rigor ortotipográfico formal en español y normas de redacción técnica desprovistas de sensacionalismo.  
  * Proveer contratos tipados para la comunicación entre los resultados neuronales y el motor de inferencia.  
* **Formato:** Script de integración en Python, base de reglas lógicas en Prolog (.pl) y especificación editorial formal.

Kanban Fase 10: Interacción de Hardware y Sistemas Embebidos

Prompt Maestro 10: Subsistema de Comunicación Serial y Control Periférico (iso-29119-testing)

* **Rol:** Lead Embedded Systems Engineer & Test Analyst.  
* **Tarea:** Programar el controlador de comunicación serial bidireccional (serial\_controller.py) y el firmware en C++ (lsp\_display\_controller.ino), integrando casos de prueba basados en partición de equivalencia.  
* **Contexto:** Cuando el sistema de IA decodifica y valida una seña, transmite comandos a través del puerto serial (PySerial) hacia una placa Arduino encargada de activar indicadores físicos o displays informativos.  
* **Restricciones:**  
  * Implementar manejo robusto de excepciones ante desconexión imprevista del puerto serial.  
  * Diseñar pruebas formales de caja negra bajo Partición de Equivalencia y Análisis de Valores Límite (BVA) para la validación de tramas seriales.  
  * Proveer código fuente tanto para el host de control como para el microcontrolador.  
* **Formato:** Código Python con gestión de puertos, código C++ estructurado para Arduino y especificación de casos de prueba IEEE 829\.

Kanban Fase 11: Auditoría Integral y Certificación de Calidad (ISO 29119 & ISO 25010\)

Prompt Maestro 11: Auditoría Global de Calidad, Trazabilidad y Release Gate (iso-25010-quality)

* **Rol:** Lead Software Quality Auditor & Release Gatekeeper (ISO 29119 / ISO 25010).  
* **Tarea:** Ejecutar la certificación integral de calidad del producto, modelado de pruebas formales, análisis de dependencias (SCA) y formulación de la Matriz de Trazabilidad 1:1.  
* **Contexto:** Ningún componente del software puede liberarse a producción sin certificar el cumplimiento de las 8 dimensiones de calidad ISO/IEC 25010, la ausencia de vulnerabilidades y la cobertura formal de pruebas.  
* **Restricciones:**  
  * Verificar cero vulnerabilidades de severidad Alta o Crítica en dependencias externas.  
  * Emitir el dictamen formal de liberación mediante un *Test Summary Report* y un reporte de cumplimiento SQuaRE.  
  * Bloquear el release si alguna de las 8 dimensiones de calidad presenta desviaciones críticas.  
* **Formato:** Estructura formal de auditoría y checklist interactivo de liberación en docs/quality/ISO-25010-AUDIT-REPORT.md.