# DAT-01 — Capturador y guardado atómico

Inicio: 2026-10-06; base DAT-04. Estado: Done para implementación y pruebas de persistencia; cámara/personas no grabadas.

Alcance: CLI `python -m src.dataset.record_samples --gloss HOLA --participant P001 --consent-ref REFERENCIA`. Preflight de cámara, cuenta regresiva de dos segundos, q/Esc cancela sin muestra, captura con timestamps y normalización compartida, remuestreo `(30,126)` float32, paths únicos y manifiesto con hash/permiso/versiones. Lock de captura evita dos escritores; escritura temporal/fsync/rename y limpieza al fallar manifiesto. Una caída de energía puede dejar huérfano: el loader debe excluirlo.

Validación: tres tests de guardado único/íntegro, entradas inválidas sin residuos y respeto del lock. Fixtures sintéticos temporales; no se guardan como corpus ni se atribuyen señas. Las funciones requieren seudónimo y referencia de permiso, sin generar consentimiento.

Límite: no se abrió webcam ni se reclutaron personas; estados web de captura no se implementan porque la ruta inicial es escritorio. CLI muestra estados pertinentes; matriz UX completa pertenece a UX-01. No afirmar validez lingüística o recolección final. Dependencias: esquema provisional VIS-04 y gobierno DAT-04 autorizados.
