# Tokens visuales y accesibilidad

Fecha: 2026-10-06. Especificación futura para web y equivalencias en escritorio.

Tokens primitivos y semánticos con nomenclatura compatible con DTCG; antes de exportar un archivo de tokens validar la versión de especificación elegida. No se genera sistema de componentes separado para el MVP.

| Variable semántica | Valor inicial | Uso |
|---|---|---|
| `--surface` | `#111827` | Panel/canvas de controles |
| `--background` | `#030712` | Fondo |
| `--text-primary` | `#FFFFFF` | Texto principal |
| `--text-secondary` | `#D1D5DB` | Metadatos funcionales |
| `--accent` | `#A7F3D0` | Acción y foco sobre superficie oscura |
| `--text-on-accent` | `#111827` | Texto en botón acentuado |
| `--warning` | `#FDE68A` | Avisos con icono/texto |
| `--danger` | `#FECACA` | Error con recuperación |
| `--radius-panel` | `12px` | Paneles |
| `--space-unit` | `4px` | Espaciado en múltiplos |
| `--content-width` | `65ch` | Texto de instrucciones |

Pares autorizados: primary/secondary/accent/warning/danger sobre surface; text-on-accent sobre accent. Medir contraste con luminancia relativa WCAG antes de aprobar; no usar blanco sobre accent ni transparencias que alteren el par aprobado. Meta ≥7:1 para texto funcional, ≥3:1 para elementos no textuales relevantes. Los valores son candidatos, sin auditoría de UI aplicada.

Definir variables en raíz, heredarlas en controles y evitar colores hex locales salvo primitivas. Inmutabilidad significa no sobrescribir tokens semánticos arbitrariamente dentro de componentes; un tema futuro puede cambiar su asignación en raíz. OpenCV recibe equivalentes BGR desde una tabla común futura; CSS no se aplica a su ventana.

Texto base web 16px y altura de línea 1.5; fuente de sistema, instrucciones ≤65ch, métricas con cifras tabulares. Reservar tamaño de video y regiones de estado; scroll interno en historial largo. Foco visible sin quedar tapado por barra sticky. Soportar zoom 200%, viewport móvil 320px y movimiento reducido. Estados nunca dependen solo de color. Meta CLS ≤0.1 en los flujos de prueba.

El contraste mejorado no demuestra conformidad AAA completa; verificar teclado, alternativas, mensajes y criterios aplicables de [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
