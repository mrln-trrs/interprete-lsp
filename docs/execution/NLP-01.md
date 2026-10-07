# NLP-01 — Plantillas y pipeline conectado

Inicio: 2026-10-06, después de LOG-01. Estado: Done para plantillas exploratorias y conexión del flujo; validación lingüística pendiente.

Alcance: traducción por siete plantillas limitadas, sin generación libre ni reordenamientos no revisados; REPOSO vacío, secuencia desconocida conserva glosas e indica ausencia de plantilla. Buffer máximo veinte glosas/diez segundos, despacho después de reposo estable, texto confirmado se conserva. Pipeline propio por sesión une inferencia → referencia de reglas → glosas → plantilla. Web puede cargar artefactos explícitos con `--model-dir`, pero sin ellos solo muestra manos y avisa modelo ausente; nunca usa un predictor fixture.

Validación: tres tests PASS de plantillas/errores, deadline/límite y cadena fixture HOLA → reposo estable → «Hola.». Las pruebas fixture verifican orquestación sin atribuir precisión de reconocimiento.

Límite: LSP-DEBT-01 conserva revisión del asesor/variantes y corpus; LOG-01 Prolog pendiente; MOD-02 impide inferencia real sin modelo válido. No se afirma traducción general. Plantillas llevan versión y linguistic_review=pending; voz/Arduino siguen opcionales.
