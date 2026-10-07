# INF-01 — Motor temporal y artefactos

Inicio: 2026-10-06, después de MOD-02. Estado: Done para motor probado con predictor inyectado; integración con modelo real pendiente.

Alcance: normalización una sola vez, buffer acotado, ventana compartida de un segundo, timestamps/frame IDs nuevos, gaps reinician ventana, modelo ausente explícito, distribución de nueve probabilidades validada y empate rechazado. Carga de artefactos exige hash, encoder, dimensiones y versiones idénticos; no acepta modelo arbitrario sin metadata.

Validación: tres tests PASS de ventana/reinicio/gap, modelo ausente y salida inválida. Predictor fixture produce una distribución determinista para verificar el flujo, nunca se expone en demo ni se guarda como modelo entrenado.

Límite: dependencia MOD-02 para inferencia real permanece pendiente por corpus y runtime; autorización exploratoria permite cerrar el componente aislado. Las salidas son candidatos; LOG-01 debe validar estabilidad y NLP-01 despachar frases. No se aprueba VAL-03 ni se inventa precisión. Integración web sin modelo conserva demo de manos.
