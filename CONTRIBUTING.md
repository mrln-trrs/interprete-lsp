# 🤝 Guía de Contribución: Intérprete LSP con IA

¡Bienvenido al equipo de desarrollo del **Intérprete de Lengua de Señas Peruana (LSP)**! Para mantener el código limpio, estructurado y sin conflictos entre módulos, sigue los lineamientos descritos en esta guía.

## Planeación y gate previo a cambios funcionales

Actualización: 2026-10-06. Consultar el [plan maestro](docs/PLAN-INTERPRETE-LSP.md), [decisiones](docs/architecture/DECISIONS.md) y [Kanban](KANBAN.md) antes de implementar. Registrar revisión del alcance, criterios VAL y esquema en M0 antes de nuevos cambios funcionales. No marcar tareas terminadas por la mera existencia de archivos; los módulos pendientes incluyen stubs.

Cada PR enlaza tarea y criterio, describe resultado, pruebas pertinentes y evidencia. Cambios de normalización, dimensión u orden de clases requieren versión de esquema y revisión de impacto sobre dataset/modelo. La aprobación de esta planeación no equivale a aprobar exposición pública o release.

---

## 🌳 Política de Ramas de Git

La política propuesta es proteger `main` y exigir revisión y pruebas antes de integrar; la protección remota no se ha verificado en esta revisión. Todo el desarrollo se realiza en ramas por característica (*feature branches*):

| Módulo | Rama Sugerida | Área de Trabajo |
|---|---|---|
| **Visión & Captura** | `feature/captura-mediapipe` | `src/vision/`, `src/dataset/` |
| **Deep Learning** | `feature/entrenamiento-lstm` | `src/training/`, `models/` |
| **Procesamiento de Lenguaje** | `feature/modulo-pln` | `src/nlp/` |
| **Hardware & Arduino** | `feature/modulo-arduino` | `src/hardware/`, `arduino/` |
| **Corrección de Bugs** | `fix/<nombre-del-bug>` | Cualquier módulo afectado |

### Flujo de Trabajo Típico:
```bash
# 1. Asegúrate de estar en main actualizado
git checkout main
git pull origin main

# 2. Crea tu rama de trabajo
git checkout -b feature/captura-mediapipe

# 3. Realiza tus cambios y confirma periódicamente
git add .
git commit -m "feat(dataset): implementar guardado de matrices npy en record_samples"

# 4. Sube tu rama al repositorio remoto
git push -u origin feature/captura-mediapipe

# 5. Abre un Pull Request (PR) en GitHub hacia main
```

---

## 🚫 Manejo Estricto de Datos y Modelos (NO subir a Git)

El archivo `.gitignore` ya está configurado para excluir:
- El entorno virtual (`venv_lsp/`).
- Videos crudos (`data/raw_videos/`).
- Coordenadas procesadas (`data/keypoints/**/*.npy`).
- Modelos entrenados pesados (`models/trained/*.h5`, `*.keras`).

### ¿Cómo compartir los datasets entre el equipo?
1. Comprime tu carpeta local `data/keypoints/` en un archivo `.zip` (ej. `dataset_lsp_v1.zip`).
2. Súbelo a un almacén privado autorizado del equipo con acceso limitado y checksum. No publicar corpus de participantes en Releases públicos; seguir consentimiento y retención del [plan de datos](docs/data/DATASET-PLAN.md).
3. Cada compañero descarga el `.zip` y lo descomprime en su ruta local `data/keypoints/`.

---

## 📝 Estándar de Mensajes de Commit (Conventional Commits)

Utiliza el estándar de commits semánticos:

- `feat(modulo):` Nueva característica (ej. `feat(vision): agregar deteccion de pose`).
- `fix(modulo):` Corrección de un error (ej. `fix(imports): corregir sys.path en main.py`).
- `docs:` Cambios o adiciones a la documentación (ej. `docs: actualizar KANBAN con tareas del Sprint 2`).
- `test:` Adición o mejora de pruebas unitarias (ej. `test: anadir pruebas para normalizacion`).
- `refactor:` Modificación de código sin cambiar funcionalidad externa.

---

## 🧪 Verificación Antes de Crear un Pull Request

Antes de solicitar la integración a `main`, ejecuta las pruebas unitarias locales en tu entorno:

```powershell
.\venv_lsp\Scripts\python.exe -m unittest discover tests/
```

Si todas las pruebas finalizan con `OK`, procede a solicitar el Pull Request y asigna a un compañero para revisión de código.
Además, ejecutar los casos pertinentes del [plan de pruebas](docs/quality/TEST-PLAN.md). Los cuatro tests de visión no cubren backend, corpus, reconocimiento, UX o hardware. No declarar certificación ISO ni ausencia de vulnerabilidades sin reporte. Para liberar, completar [trazabilidad](docs/quality/TRACEABILITY-MATRIX.md) y [checklist de calidad](docs/quality/ISO-25010-AUDIT-REPORT.md).
