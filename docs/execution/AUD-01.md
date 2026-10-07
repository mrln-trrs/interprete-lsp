# AUD-01 — Voz local opcional en web

Inicio: 2026-10-06, después de UX-01. Estado: parcial: salida implementada, reproducción/browser NOT_RUN.

Alcance: checkbox opt-in, solo texto confirmado, voz española marcada localService por navegador, una utterance vigente (cancelar anterior), parar/limpiar cancela audio; ausencia/fallo conserva texto. No activar audio al abrir, no enviar texto a un servicio externo del proyecto ni seleccionar voz remota. El navegador/SO debe disponer de voz local; si no, texto base sigue funcional.

Adaptación de pila: para cliente web se usa SpeechSynthesis del navegador en lugar de pyttsx3 del servidor, evitando que la laptop hable por todos los clientes. Pyttsx3 queda como posibilidad futura de consola de escritorio. Prueba manual futura: activar con voz local española, confirmar frase, cambiar/parar/cancelar y verificar ausencia de cola/voz al mostrar candidatos.

Límite: no se reprodujo audio ni se simuló validación física; Edge automático rechazado por política. El texto confirmado de modelo real depende MOD-02. No se afirma equivalencia lingüística de las plantillas.
