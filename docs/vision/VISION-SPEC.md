# Visión y normalización espacial

Fecha: 2026-10-06. Implementación existente, aceptación pendiente.

Pipeline: BGR → RGB → MediaPipe → lateralidad → bloque izquierdo 63 + derecho 63 → centro muñeca → escala palma → float32 126D → timestamps → ventana de 30 instantes. Una mano ausente produce su bloque cero; ambas ausentes mantienen 126 ceros. Validar forma, finitud y escala degenerada antes de inferencia.

La función actual usa muñeca 0 y nudillo medio 9, distancia máxima como fallback y umbral 1e-4. No garantiza invarianza de iluminación, rotación u oclusión. No tiene validación exhaustiva de NaN/rank. Pruebas adicionales deben cubrir arrays `(126,)`, `(21,3)`, entradas inválidas, transformaciones de traslación/escala positivas, coordenadas coincidentes y ausencia unilateral. Tolerancia propuesta: 1e-5 para transformaciones bien condicionadas.

Orden espacial inmutable: Left seguido de Right según convención validada de imagen espejada. Ensayar mano física izquierda y derecha en webcam y ambas cámaras móviles; no deducir corrección solo de etiqueta MediaPipe. Registrar convención en manifiesto.

Evaluar pérdida de posición de muñecas y relación entre manos al normalizar por separado; comparar baseline actual con features que preserven esa información. Esquema ampliado requiere ADR y corpus nuevo o transformación reproducible. Para señas con componentes faciales/corporales fuera del esquema, reducir alcance documentadamente.

Performance: medir cinco minutos con equipo/resolución/versiones y carga; reportar captura efectiva, procesamiento p50/p95, RTT y frames descartados. Objetivos y política de timestamps: [plan maestro](../PLAN-INTERPRETE-LSP.md). Liberar cámara/detector al cerrar, cancelar o fallar. El render ocupa un área de relación de aspecto reservada; etiquetas y estadísticas no alteran su tamaño.
