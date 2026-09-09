# 🤝 Guía de Contribución: Intérprete LSP con IA

¡Bienvenido al equipo de desarrollo del **Intérprete de Lengua de Señas Peruana (LSP)**! Para mantener el código limpio, estructurado y sin conflictos entre módulos, sigue los lineamientos descritos en esta guía.

---

## 🌳 Política de Ramas de Git

La rama `main` está protegida y solo debe contener código probado y listo para producción o demostración. Todo el desarrollo se realiza en ramas por característica (*feature branches*):

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
2. Súbelo a la carpeta compartida de **Google Drive** del equipo o a los **Releases** de GitHub.
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
