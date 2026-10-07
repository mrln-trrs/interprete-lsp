# Fuentes gratuitas verificadas

Consulta: 2026-10-06. Referencia inicial oficial: [MINEDU, Lengua de señas peruana: guía para el aprendizaje, vocabulario básico (2015)](https://repositorio.minedu.gob.pe/handle/20.500.12799/5545). El catálogo describe vocabulario y componentes manuales/corporales; el acceso directo mostró verificación de seguridad, por lo que no se atribuyen páginas ni gestos específicos sin leer el PDF. Es orientación lingüística, no un conjunto de secuencias etiquetadas.

| Fuente | Acceso y licencia observados | Uso en el prototipo |
|---|---|---|
| [PUCP-DGI156 / PeruSIL](https://datos.pucp.edu.pe/dataset.xhtml?persistentId=hdl:20.500.12534/OJYYYS) | API pública respondió; licencia del dataset CC0 1.0. Videos, SRT y keypoints disponibles | Prioridad para explorar glosas y convertir RGB a esquema propio |
| [VideoLSP10](https://github.com/videoLSP/VideoLSP10) | README indica uso académico no comercial; texto también exige conservar licencia en derivados | Fuente candidata; verificar archivo LICENSE y cobertura antes de importar |
| [SIGNO-PERU-ISO](https://zenodo.org/records/18990737) | Metadatos públicos, archivos restringidos con acuerdo de uso | No descargar ni pedir acceso automáticamente; excluido de datos disponibles |
| [Dictionary-LSP PUCP](https://github.com/lab-humanidades-digitales/Dictionary-LSP) | Código MIT; esa licencia no prueba permiso de todo video externo | Referencia de software; no adoptar modelo/datos sin verificar alcance |

PUCP: API `https://datos.pucp.edu.pe/api/datasets/:persistentId?persistentId=hdl:20.500.12534/OJYYYS`. Archivos observados: `SRT.tar` ID 14429 (196096 bytes), `Videos.tar` ID 14427 (1078811648 bytes), `Keypoints.tar` ID 14428 (723681280 bytes), tabla ID 14626. Se descargaron anotaciones y tabla en `data/raw_videos/perusil/`, ignorado por Git. La tabla permite agrupar por participante; los keypoints ajenos no se cargan como pickle ni se asumen equivalentes a 126D.

Regla de ingreso: origen/fecha/URL/licencia/hash registrados, etiqueta explícita mapeada de forma revisable, identidad de grupo seudónima preservada y sin ejecutar pickle ajeno. No reutilizar señas de otros países como LSP ni inferir etiquetas de títulos de video o frases españolas. Material accesible en internet sin permiso de reutilización queda fuera del corpus hasta aclaración. Corpus público con términos de uso verificables no requiere inventar consentimientos individuales; nuevas grabaciones sí requieren consentimiento.
