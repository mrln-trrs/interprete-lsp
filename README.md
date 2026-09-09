# Intérprete de Lengua de Señas Peruana (LSP) con IA

Repositorio modular para el desarrollo de un intérprete de Lengua de Señas Peruana basado en visión artificial, Deep Learning (LSTM) y PLN contextual.

## Estructura del Proyecto

- `config/`: Configuraciones globales y mapa de señas/acciones.
- `data/`: Datos de video y coordenadas procesadas (.npy) [ignorado por git].
- `models/`: Modelos entrenados (.h5 / .keras) y pesos [ignorado por git].
- `src/`: Código fuente modular (visión, dataset, entrenamiento, PLN, hardware, main).
- `arduino/`: Firmware C++ para visualización en hardware.

## Entorno Virtual

El entorno virtual se encuentra en `venv_lsp/` (Python 3.11).

Para activarlo en Windows (PowerShell):
```powershell
.\venv_lsp\Scripts\Activate.ps1
```
