# LOG-01 — Reglas y deduplicación

Inicio: 2026-10-06, después de INF-01. Estado: parcial para prompt Prolog; referencia Python operativa y probada.

Alcance: umbral 0.85 inclusivo, diez decisiones de frames nuevos, reinicio ante confianza baja/cambio/gap >200 ms; una glosa por gesto estable, REPOSO no verbalizado y reposo ≥500 ms con diez decisiones rearma repetición. Base Prolog cerrada y puente opcional con argumentos numéricos/allowlist y timeout 50 ms, sin consultas de usuario.

Validación: tres tests de confianza/estabilidad, deduplicación/rechazo de frame repetido y reposo/gap. No se exige modelo para probar reglas, pero inferencia real depende MOD-02. SWI-Prolog no acreditado; el puente por proceso es un spike de equivalencia, no ruta obligatoria por frame por su sobrecosto. Timeout rechaza, nunca inventa aceptación.

Límite: prototipo usa referencia Python explícita (ADR-08 provisional); paridad/instalación Prolog y rendimiento pendientes. No afirmar que Prolog está integrado o probado al validar la referencia. Las plantillas serán provisionales hasta asesor.
