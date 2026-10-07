# Deuda técnica del prototipo exploratorio

Actualizado: 2026-10-06. El usuario autorizó avanzar con fuentes gratuitas, referencia oficial peruana y revisión de asesor futura. Arduino queda fuera de la entrega actual. Esta decisión cambia las dependencias de exploración, no convierte pruebas sintéticas en evaluación lingüística.

| ID | Deuda / condición | Tratamiento y gate |
|---|---|---|
| LSP-DEBT-01 | Sin revisión presencial de asesor/personas usuarias | Referencia MINEDU como orientación; revisión humana y variantes regionales antes de afirmar traducción validada |
| VIS-DEBT-01 | Features de manos pierden ubicación relativa y componentes no manuales | Esquema `hands-126-v1` provisional para prototipo; ablación con corpus antes de congelarlo para release |
| DAT-DEBT-01 | Fuentes abiertas no equivalen al corpus de nueve clases | Verificar acceso/licencia y etiquetas; no duplicar ejemplos para alcanzar cuotas ni convertir dibujos en movimientos reales |
| ML-DEBT-01 | Optree/SSL bloqueados por Windows | Linux CI nativo validado; Windows pendiente de runtime permitido. No modificar controles ni fingir entrenamiento |
| SEC-DEBT-01 | Protobuf con CVE-2026-0994 alto | Migrar pila compatible y probar; release/exposición pública bloqueados |
| UX-SEC-01 | JS/CSS principales extraídos; quedan atributos style inline | Retirar estilos inline restantes y endurecer style-src antes de release |
| HW-DEBT-01 | Arduino futuro sin placa/display definidos | Deshabilitado; protocolo/simulador pueden prepararse, integración real fuera del prototipo |

Validación provisional: pueden implementarse y probarse software, contratos, corpus sintético estructural, reglas y simuladores. Los gates VAL-02 (corpus real), VAL-03 (precisión), asesor, hardware incluido y seguridad alta conservan evidencia pendiente. Una tarea se puede cerrar para entrega de software explícitamente acotada; su requisito global no queda aprobado automáticamente.
