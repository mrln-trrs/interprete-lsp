# Auditoría de calidad y dictamen de liberación

Fecha: 2026-10-06. Candidato técnico: `e4880b7bab81d2d10b5824c385330d33041a8f2d`; cierre documental posterior en REL-01. Responsable de revisión técnica: Codex, bajo autorización del usuario. **Dictamen: NO APTO para liberar el intérprete completo ni exponerlo públicamente.** No constituye certificación ISO.

## Evidencia ejecutada

[CI Linux/Python 3.11](https://github.com/mrln-trrs/interprete-lsp/actions/runs/37558676708) terminó con éxito sobre el candidato: suite de 43 tests, smoke nativo y contraste. Incluye LSTM/GRU compilados, probabilidades y guardado/carga de modelos de prueba sin entrenamiento lingüístico. Windows: 42 PASS y un SKIP por DLL optree bloqueada; SSL también está bloqueado. Integración real JPEG/OpenCV/MediaPipe/API probada sin abrir cámara. JavaScript validado sintácticamente; aceptación en navegador no ejecutada.

Secret scan del historial alcanzable actualizado sin coincidencias. SCA/SBOM consultan advisories de las 73 dependencias del perfil Windows: protobuf 4.25.9 mantiene CVE-2026-0994 alto. Sus versiones corregidas son incompatibles con restricciones actuales; no se fuerza el upgrade. SCA Linux actualizado: 68 dependencias consultadas, una afectada (protobuf), cero consultas fallidas. Ambos perfiles conservan el mismo bloqueo alto; informes Linux separados en docs/security/evidence/linux. Informes en `docs/security/evidence`; ausencia de hallazgos de secretos no equivale a ausencia de vulnerabilidades.

## Evaluación del producto

| Característica | Evidencia y límite |
|---|---|
| Adecuación funcional | Pipeline y plantillas probados; sin corpus completo, modelo real ni métricas independientes |
| Eficiencia | Una petición por cliente y cuotas; FPS/latencia real NOT_RUN |
| Compatibilidad | Linux nativo PASS; Windows ML parcial; navegador/Prolog pendientes |
| Interacción | Siete estados, foco y controles implementados; contraste de textos ≥7:1; CLS/lector/zoom pendientes |
| Fiabilidad | Recuperación y aislamiento cubiertos por suite; experiencia real de cámara/red pendiente |
| Seguridad | DTO estricto, origen, sesión, límites y errores probados; protobuf alto bloquea release |
| Mantenibilidad | Módulos, locks, CI y trazabilidad presentes; integración operativa aún exploratoria |
| Flexibilidad | Modelo explícito y voz opcional; Arduino diferido por usuario |
| Seguridad operacional | Rechazo de incertidumbre y ausencia de texto inventado; falsas emisiones reales sin evaluar |

## Bloqueos y tratamiento

1. DAT-03: obtener corpus autorizado con cobertura de nueve clases, cuotas y participantes suficientes. Anotaciones PERUSIL inspeccionadas; tar RGB truncado no aceptado.
2. MOD-02/VAL-03: entrenar y comparar modelos con partición por persona, evaluación independiente y métricas reales.
3. SEC-DEBT-01: resolver compatibilidad de protobuf corregido y repetir SCA de todos los perfiles incluidos.
4. UX/QA: navegador, accesibilidad, voz, cámara y benchmark reales. La revisión automática rechazó el lanzamiento de Edge; no se atribuyen resultados al harness.
5. LOG-01: runtime y paridad Prolog pendientes; Python es la referencia ejecutada.
6. Validación lingüística: MINEDU como referencia inicial; asesor futuro según instrucción del usuario. Esa deuda permite avanzar el prototipo, pero no acredita aceptación lingüística.

Arduino no integra este candidato y no bloquea el prototipo. No se han fabricado consentimientos, corpus, precisión ni validaciones humanas. El gate se reevalúa al resolver estos puntos y actualizar la matriz VAL. Demo local exploratoria limitada a capacidades probadas; el dictamen no autoriza despliegue público.
