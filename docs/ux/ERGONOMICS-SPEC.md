# Ergonomía de consola y estados

Fecha: 2026-10-06. Diseño pendiente de implementación y validación con operadores.

Vista dual: panel de cámara y landmarks; panel de glosa candidata, texto confirmado e historial de sesión. Barra de acciones sticky con iniciar/detener, limpiar salida y configuración opcional. En móvil apilar conservando orden de lectura; video con espacio reservado. Historial desplaza dentro de panel y no mueve controles. `z-index:30` es propuesta web, no regla de escritorio.

Flujo: abrir → revisar preflight → conceder permiso explícito → iniciar captura → ver estado/candidato → recibir texto validado → detener. Iniciar/detener requiere una acción cada uno; cambio de cámara ≤2 acciones después de permisos. No contabilizar diálogo de permisos del SO como clic controlado por la app. No activar cámara ni audio automáticamente.

Preflight identifica cámara, modelo compatible y serial: listo/no configurado/fallido con texto e icono. Serial deshabilitado no bloquea texto. Modelo ausente permite demo de manos claramente rotulada; no mostrar una falsa traducción.

| Estado | Entrada | Presentación / acción | Salida |
|---|---|---|---|
| Idle | Inicio o parada | Iniciar; permiso y privacidad | Loading |
| Loading | Abrir cámara/modelo, cuenta regresiva | Mensaje y cancelar | Success, Error, Offline |
| Success | Flujo válido o muestra guardada | Métricas/texto/confirmación discreta | Partial, Empty, Error, Idle |
| Empty | Sin manos, datos o glosas | Explicar ausencia; no inventar texto | Success o Idle |
| Error | Permiso denegado, archivo corrupto, fallo local | Motivo seguro y reintentar/cancelar | Loading o Idle |
| Partial | Ventana incompleta, huecos, confianza baja o serial fallido | Mantener último texto confirmado; no emitir candidato | Success, Error, Offline |
| Offline | Red/servidor indisponible | Detener envío; reconexión limitada y manual | Loading o Idle |

Offline describe conectividad; fallos de cámara local son Error. Al detener borrar buffers candidatos y liberar tracks; mantener solo texto ya confirmado hasta limpiar. Nunca reenviar frames en cola tras reconectar. Captura dataset solo permite guardar secuencia íntegra; cancelación no produce `.npy` parcial.

Keyboard-first: controles nativos y orden Tab lógico, Enter/Espacio para activación; Escape cancela cuenta regresiva/cierra diálogo y devuelve foco al origen. Atajos opcionales Alt+I iniciar/parar, Alt+L limpiar con aviso si corresponde; documentarlos y no interceptarlos dentro de campos editables. En OpenCV `q`/Esc continúan como salida, sin prometer capacidades semánticas de navegador.

Diálogos modales contienen foco mientras están abiertos y siempre tienen cierre por teclado; no hay atrapamiento sin salida. Actualizaciones agregadas en `aria-live=polite`, errores urgentes como alerta; no anunciar cada frame. Pruebas: teclado, lector de pantalla, permisos denegados, reconexión, rotación móvil, zoom, siete estados y preservación espacial.
