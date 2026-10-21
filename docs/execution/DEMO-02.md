# DEMO-02 — Banco de medios: números, abecedario y meses

Inicio: registrado el 2026-10-21 sobre trabajo local sin commit; base `bcc827e`. Estado: Done para software de demostración; validación lingüística y procedencia de medios pendientes.

Alcance: motor `src/inference/media_bank.py` con prototipos posturales y temporales extraídos por `scripts/build_media_bank.py` de medios locales (`C:\proyectos\media`): números 1–20, abecedario A–Z + Ñ y meses (variante completa en video y abreviada). Bancos versionados en `models/gestures/{numbers,alphabet,months}_bank.json` y secuencias derivadas en `data/keypoints_media/` (solo keypoints, sin imágenes). Activación explícita `--media-demo`, con `--media-category` para limitar categoría. Vocabulario extendido a 68 clases en `config/actions.py` (`EXTENDED_ACTIONS`); el validador acepta esas clases.

Dependencias: INF-01, LOG-01, NLP-01 y UX-01. LOG-01 se ajustó el 2026-10-21 para que Prolog acepte las mismas 68 clases (antes divergía: solo 0–8).

Validación: cinco pruebas de `tests/test_media_bank.py` (los tres pasos, invariancia espejo y pipeline que reconoce y vacía) dentro de la suite completa: 57 tests PASS, 0 SKIP en Linux aarch64 (OrbStack) con `LSP_NATIVE_ML_TESTS=1` y SWI-Prolog. Demo levantada en contenedor con `--media-demo`: GET 200 y sesión 201.

Límite: es comparación con prototipos, no un modelo entrenado ni precisión medida. Los medios de origen no están en el repositorio y su licencia/permiso de uso no está documentado (MEDIA-DEBT-01). Prueba física con cámara y validación por persona usuaria de LSP pendientes. No cambia el dictamen de release.
