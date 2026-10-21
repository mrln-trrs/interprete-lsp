# LOG-01 — Reglas y deduplicación

Inicio: 2026-10-06, después de INF-01. Estado: parcial para prompt Prolog; referencia Python operativa y probada.

Alcance: umbral 0.85 inclusivo, diez decisiones de frames nuevos, reinicio ante confianza baja/cambio/gap >200 ms; una glosa por gesto estable, REPOSO no verbalizado y reposo ≥500 ms con diez decisiones rearma repetición. Base Prolog cerrada y puente opcional con argumentos numéricos/allowlist y timeout 50 ms, sin consultas de usuario.

Validación: tres tests de confianza/estabilidad, deduplicación/rechazo de frame repetido y reposo/gap. No se exige modelo para probar reglas, pero inferencia real depende MOD-02. SWI-Prolog no acreditado; el puente por proceso es un spike de equivalencia, no ruta obligatoria por frame por su sobrecosto. Timeout rechaza, nunca inventa aceptación.

Límite: prototipo usa referencia Python explícita (ADR-08 provisional); paridad/instalación Prolog y rendimiento pendientes. No afirmar que Prolog está integrado o probado al validar la referencia. Las plantillas serán provisionales hasta asesor.

## Avance 2026-10-21

Runtime Prolog acreditado en Linux aarch64 (OrbStack, SWI-Prolog 9.2.9). Se halló divergencia: Python aceptaba las 68 clases de `EXTENDED_ACTIONS` y `lsp_rules.pl` solo 0–8. Corregido con `class_count(68)` y `allowed_class/1` por rango; `test_prolog_vocabulary_matches_python` impide que vuelvan a separarse (no requiere swipl). `test_prolog_parity` compara 105 casos límite (clases −1, 0, 1, 8, 9, 67, 68; confianza 0.8499/0.85/0.8501/1.0/1.0001; estabilidad 9/10/11): PASS, iguales a la referencia Python. Latencia por consulta (proceso nuevo) p50 4.9 ms, p95 5.2 ms, máximo 5.5 ms en 20 llamadas; con el timeout de 50 ms acepta 10/10. `prolog_accepts` admite `timeout` explícito; por defecto sigue 50 ms. Estado: Done para paridad y runtime; Prolog sigue fuera del camino de inferencia en vivo (la demo usa la referencia Python) y Windows no se probó.
