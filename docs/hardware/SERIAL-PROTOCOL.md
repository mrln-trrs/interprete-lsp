# Protocolo serial y plan de integración

Fecha: 2026-10-06. Host pendiente; firmware solo lee líneas. Hardware deshabilitado en configuración actual.

Baseline propuesto: PySerial, 9600 baudios, puerto explícito, timeout lectura/escritura 200 ms y comandos de indicadores. Placa, LCD, dimensiones y codificación del display pendientes de selección; texto libre en LCD queda fuera del protocolo inicial hasta resolverlos.

Trama ASCII hasta 64 bytes incluyendo LF: `V1|SEQ|CMD|ARG\n`. SEQ entero decimal 0–65535; CMD `PING`, `GLOSS` o `CLEAR`; ARG `-` en PING/CLEAR y ID 0–8 en GLOSS según ACTIONS versionado. Respuesta `V1|SEQ|ACK|-\n` o `V1|SEQ|ERR|CODE\n`, CODE allowlist `FORMAT`, `VERSION`, `RANGE`, `COMMAND`, `BUSY`. Rechazar caracteres de control distintos de LF, más de cuatro campos y líneas >64 bytes; vaciar hasta LF después de overflow, sin desbordar memoria.

GLOSS solo se envía después de validación lógica. No transmite video, keypoints ni identidad. Secuencia repetida con mismo contenido devuelve ACK sin repetir efecto; misma SEQ con distinto contenido produce ERR. Secuencias incrementan con wrap; mantener solo última trama válida por conexión y reiniciar estado al reconectar con handshake PING. Protocolo no proporciona autenticación/CRC: usar enlace USB físico controlado y documentar limitación.

Host no bloquea captura: cola de una salida más reciente, una trama pendiente, máximo un reintento tras timeout solo con deduplicación activa. A 9600 baudios, 64 bytes ocupan aproximadamente 67 ms con 8N1; verificar timeouts en placa real. Desconexión cierra puerto, marca Partial y conserva texto; reconexión manual o backoff acotado sin bucle infinito. Tras reconectar descartar salida antigua, no reproducir mensajes pendientes.

| Caso / técnica | Entrada | Resultado |
|---|---|---|
| HW-T01 / equivalencia | Comandos válidos con ARG esperado | ACK y efecto una vez |
| HW-T02 / BVA | SEQ -1, 0, 65535, 65536 | Solo 0/65535 válidos |
| HW-T03 / BVA | GLOSS -1, 0, 8, 9 | Solo 0/8 válidos |
| HW-T04 / BVA | Longitudes 63, 64, 65 bytes | 63/64 admitidas si sintaxis válida, 65 rechazadas |
| HW-T05 / equivalencia | Campo ausente/extra, versión/CMD inválidos, sin LF | ERR o timeout acotado, sin efecto |
| HW-T06 / resiliencia | Desconectar durante escritura/ACK | Estado degradado, sin bloquear cámara |
| HW-T07 / idempotencia | Repetir SEQ/contenido; alterar contenido | ACK sin repetición / ERR |

Cada caso registra fixture, setup, esperado, obtenido, fecha, commit y evidencia. Ejecutar primero con simulador/loopback y luego placa real; simulación no certifica integración física. Formato de casos inspirado en documentación de pruebas tradicional e ISO 29119, sin afirmar certificación IEEE 829.
