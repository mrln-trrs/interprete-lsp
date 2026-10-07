# MOD-01 — Baseline LSTM/GRU

Inicio: 2026-10-06; base `0187ab9`. Estado: parcial: arquitectura implementada, compilación/ejecución de modelo bloqueadas por ENV-03.

Alcance: constructor TensorFlow/Keras con entrada `(30,126)`, recurrente LSTM o GRU 64, L2 1e-4, Dropout 0.3, Dense32 y Softmax9; Adam1e-3 y sparse categorical crossentropy. Validación de forma/clases/dropout antes de importar runtime nativo; error explícito si Keras no está disponible. No actualizar dependencia para eludir controles Windows.

Validación: dos pruebas de configuración PASS (rechazo de esquemas incompatibles y baselines permitidos), compilación sintáctica. Esto no acredita entrenamiento, compilación Keras ni comparación de F1. El smoke ENV-03 demuestra el bloqueo real de optree, por lo que MOD-01 no se marca Done completo.

Dependencia: VIS-04 provisional habilita implementación; ENV-03 habilitará ejecución real. Corpus DAT-03 no se necesita para definir red, pero sí para comparar desempeño. No guardar modelos aleatorios como entrenados.
