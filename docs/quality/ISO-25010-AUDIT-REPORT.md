# Auditoría de calidad y dictamen de liberación

Fecha: 2026-10-06. Candidato: árbol de trabajo inspeccionado sobre HEAD `506d28c`; cambios documentales sin commit. Dictamen: **NO APTO para release del intérprete completo ni exposición pública sin controles**. La demo de detección existente no acredita reconocimiento de señas.

Este es un informe inicial de brechas y un formato de auditoría futura, no certificación. El prompt menciona ocho características; se actualiza a las nueve del modelo de producto [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), manteniendo orientación SQuaRE. No se ha evaluado el texto normativo completo.

| Característica | Evaluación requerida | Estado / brecha |
|---|---|---|
| Adecuación funcional | Nueve clases y frases revisadas, VAL-03 | Pendiente: no hay clasificador/PLN operativo |
| Eficiencia de desempeño | FPS, p95, CPU/RAM y cola | Pendiente: cifras históricas sin reporte actual |
| Compatibilidad | SO/runtime, navegador, esquema y serial | Pendiente: entorno y round-trip no verificados |
| Capacidad de interacción | Teclado, foco, estados y accesibilidad | Pendiente: UI existente sin auditoría |
| Fiabilidad | Desconexiones, recuperación y limpieza | Pendiente: pruebas integrales |
| Seguridad | STRIDE, secretos, SCA y controles web | Pendiente: límites/autorización no observados |
| Mantenibilidad | Modularidad, contratos, tests y trazabilidad | Parcial: estructura presente, varios stubs |
| Flexibilidad | Configuración y adaptación de hardware/captura | Pendiente: validar perfiles sin cambiar fuente |
| Safety (seguridad operacional) | Rechazo prudente, avisos y alcance no crítico | Pendiente: validación de falsas emisiones |

## Test Summary Report inicial

- Alcance de esta revisión: archivos y documentación; no ejecución del producto.
- Suite localizada: cuatro pruebas en `tests/test_vision.py`, sin ejecución actual acreditada.
- Entrenamiento/evaluación: no realizados; sin métricas de reconocimiento verificables.
- Secret scan completo y SCA: no realizados; ausencia de vulnerabilidades no demostrada.
- Hardware: firmware básico inspeccionado; sin placa, loopback o display probados.
- Desviaciones críticas: subsistemas centrales no implementados; seguridad de exposición pública pendiente; dataset y test independiente no acreditados.

## Gates de entrega

Gate documental: especificaciones, Kanban y trazabilidad disponibles; revisión del equipo pendiente. Gate demo local: solo capacidades efectivamente probadas y rotuladas, cámara consentida y sin exposición. Gate demo remota: SEC-01 a SEC-07 aprobados, TLS y servidor apropiado, recursos limitados y privacidad visible. Gate intérprete MVP: VAL-01 a VAL-05 aprobados, incluyendo revisión lingüística y evaluación independiente. No heredar aprobación del túnel histórico.

- [ ] Commit candidato, versiones y hashes identificados.
- [ ] Plan/ADR revisados y alcance de release declarado.
- [ ] Consentimiento y eliminación de datos verificados.
- [ ] Matriz de trazabilidad con evidencia PASS para requisitos aplicables.
- [ ] Pruebas unitarias, integración, sistema, accesibilidad y benchmark aprobadas.
- [ ] Reporte de modelo independiente y plantillas revisadas.
- [ ] Secret scan e historial alcanzable auditados; secretos confirmados rotados.
- [ ] SCA/SBOM actualizado; cero altas/críticas abiertas.
- [ ] Sin defectos críticos; riesgos residuales con propietario y tratamiento.
- [ ] Texto base funciona al fallar audio/serial; hardware real probado si se incluye.
- [ ] Manual de operación, rollback y limpieza de sesiones/datos probado.
- [ ] Revisor y responsable de release registran dictamen, fecha y evidencia.

Plantilla de cierre: candidato; alcance incluido/excluido; entorno; pruebas ejecutadas/aprobadas/fallidas/no ejecutadas; defectos; métricas; seguridad; riesgos residuales; decisión APTO/NO APTO; responsables; enlaces a evidencia. Auditoría académica interna no implica certificación ISO por un organismo acreditado.
