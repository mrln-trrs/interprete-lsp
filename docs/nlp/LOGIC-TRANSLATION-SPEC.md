# Reglas lógicas y traducción editorial

Fecha: 2026-10-06. No existe base Prolog; `translator.py` es un stub.

Contrato de entrada: clase del vocabulario, confianza finita [0,1], frame_id creciente, timestamp, versión de modelo. Contrato de salida: glosa aceptada con evidencia temporal o rechazo tipado. Umbral ≥0.85 y al menos diez decisiones consecutivas de una clase sobre frames nuevos. Cambio de clase, caída de confianza, reinicio de sesión o hueco >200 ms reinicia estabilidad. Un empate/ambigüedad rechaza; umbrales adicionales de margen se calibran en validation y se versionan.

Estado: candidato → estable → emitido → espera de liberación. Tras emitir una glosa no repetirla mientras continúe el mismo gesto; permitir repetición solo después de REPOSO confirmado o pausa mínima propuesta de 500 ms validada temporalmente. REPOSO no se verbaliza. El buffer de frase se despacha al terminar pausa confirmada o por acción explícita; definir tiempo máximo de frase propuesto de diez segundos y máximo 20 glosas, con aviso al excederlo.

Spike Prolog: base prevista `src/logic/lsp_rules.pl` y puente tipado a Python, consulta parametrizada con clases allowlist, timeout propuesto 50 ms y manejo de fallo sin emitir glosa. Nunca interpolar texto cliente en consultas. Comparar salidas contra referencia determinista Python en casos de límites 0.8499/0.85/0.8501 y 9/10/11 decisiones. Si SWI-Prolog no se puede integrar, registrar ADR y limitar demo a referencia, manteniendo integración del prompt pendiente.

PLN inicial por diccionario/plantillas revisadas: `[YO, QUERER, AGUA]` → «Yo quiero agua.»; `[HOLA]` → «Hola.»; `[GRACIAS]` → «Gracias.». Las variantes de orden solo se incorporan tras aprobación de asesor LSP; no afirmar equivalencia lingüística general. Secuencias desconocidas muestran glosas y «Sin plantilla disponible», sin añadir intención ni completar frases libres.

Editorial: español con tildes, mayúscula inicial y puntuación final; glosas internas en MAYÚSCULAS_CON_GUION_BAJO; separar candidata de confirmada. Informar «Confianza insuficiente» y «Modelo no disponible» con precisión. No presentar probabilidades como garantía ni manos detectadas como señas reconocidas. Audio solo del texto confirmado, habilitado explícitamente, cola acotada y cancelable; fallo de voz conserva texto.

Aceptación: reglas de límite, deduplicación, pausas, frase desconocida, timeout Prolog y limpieza de sesión; revisión lingüística documentada del glosario y de cada plantilla.
