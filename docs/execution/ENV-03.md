# ENV-03 — Entorno reproducible y límite de validación

Inicio: 2026-10-06; base `78f4b43`, PLN-01 revisado. Estado: **parcial / bloqueado por política Windows para SSL y optree**.

Alcance realizado: Python 3.11.15 instalado con uv 0.12.1, entorno `venv_lsp`, lock completo con hashes y listado resuelto para Windows x64/Python 3.11. Flask fijado en 3.1.3. Se elimina `opencv-python` duplicado y se conserva `opencv-contrib-python==4.11.0.86`, requerido por MediaPipe; reinstalado tras retirar el paquete superpuesto. Se agregan exclusiones de herramientas y metadatos privados. No se modifican modelos ni se recopilan datos.

Validación: `uv pip check --python venv_lsp/Scripts/python.exe` sin incompatibilidades declaradas; cuatro tests de visión PASS (0.274 s). OpenCV 4.11.0 y MediaPipe 0.10.14 importan y procesan imagen sintética. TensorFlow 2.16.1 importa, pero Keras no logra importar optree: la DLL `_C` es bloqueada por Control de aplicaciones. `_ssl` también está bloqueado; no se deshabilita la política ni se reemplaza TLS por conexiones inseguras. Un intento de instalador alternativo firmado fue rechazado automáticamente con «blocked by policy» y no se reintentó.

Reproducción: crear entorno con Python 3.11 aprobado, `uv pip sync requirements.lock --python venv_lsp/Scripts/python.exe --require-hashes`, `python -m scripts.check_environment --output docs/execution/environment.json`, `python -m unittest discover -s tests -p test_vision.py`. El lock está validado solo para este perfil Windows; otros SO requieren resolver/verificar su propio perfil.

Límite: no declarar ENV-03 Done ni entrenamiento compatible hasta que el equipo use un runtime permitido por su política que cargue SSL y optree y pase el smoke completo. Los controles del sistema no se eluden. API-01 solo depende de PLN-01 y se puede probar con Flask sin la red neuronal; SEC-09 puede auditar el lock ya resuelto, indicando esta excepción de dependencia. VIS-04 y ML mantienen el gate técnico pendiente.

## Evidencia posterior de CI

2026-10-06: [Linux/Python 3.11](https://github.com/mrln-trrs/interprete-lsp/actions/runs/37558676708), candidato `e4880b7`, resultado SUCCESS. Suite de 43 tests y smoke nativo aprobados; LSTM y GRU compilan y sus artefactos de prueba se guardan/cargan. ENV-03 queda validado para Linux y MOD-01 para arquitectura nativa. No es entrenamiento del vocabulario ni comparación de precisión. Windows y los límites de aceptación de QA permanecen como se describen arriba.
