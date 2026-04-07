# CheckerIT

CheckerIT es una aplicación web full-stack para jugar a Damas Chinas. El frontend está desarrollado con React y el backend con Django y Django REST Framework.

## Alcance y características principales

- Gestión de partidas: creación, finalización y control de turnos.
- Registro de movimientos con validación de reglas en el backend.
- Interfaz de usuario con tablero, tutorial y pantallas de juego.
- Soporte de jugadores humanos e inteligencia artificial.
- Agente Inteligente con dos niveles: heurística y MCTS (dificultad “Difícil”).

## Arquitectura

- Frontend: React 18, React Router, Axios.
- Backend: Django 5.0, Django REST Framework, django-cors-headers.
- Persistencia:
    - Por defecto: SQLite (configuración de desarrollo).
    - Opcional: PostgreSQL mediante variables de entorno.

## Requisitos

- Python 3.8 o superior
- Node.js 14 o superior
- npm
- (Opcional) PostgreSQL 12 o superior

## Instalación y ejecución (Windows)

### Arranque rápido (recomendado)

Desde la raíz del proyecto puedes levantar backend y frontend con un único script:

```powershell
./scripts/dev.ps1
```

Opciones útiles:

```powershell
./scripts/dev.ps1 -BackendOnly
./scripts/dev.ps1 -FrontendOnly
./scripts/dev.ps1 -SkipInstall
./scripts/dev.ps1 -OpenBrowser
```

Notas:

- El script detecta un virtualenv existente en `.venv` (raíz) y, si no existe, lo crea.
- Mantiene compatibilidad con entornos antiguos (`backend/.venv` o `backend/venv`) si ya los tienes.

### Backend (Django) — ejecución manual

Desde la raíz del proyecto:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

El backend queda disponible en `http://localhost:8000` y la API en `http://localhost:8000/api/`.

### Frontend (React) — ejecución manual

En una terminal independiente, desde la raíz del proyecto:

```powershell
cd frontend
npm install
npm start
```

El frontend queda disponible en `http://localhost:3000`.

## Testing

### Backend (pytest)

Ejecuta el suite de tests automáticos (unitarios + integración) desde `backend/`:

```powershell
cd backend
python -m pytest -q
```

### Testing del Agente Inteligente (carpeta IA)

Estos 3 scripts se ejecutan como comprobaciones reproducibles (no se lanzan con `pytest`).
Desde la raíz del repositorio, en Windows, ejecútalos con el Python del venv:

```powershell
C:/Users/JoséManuel/Documents/TFG/CheckerIT/.venv/Scripts/python.exe \backend\game\tests\ai\test_heuristica.py
C:/Users/JoséManuel/Documents/TFG/CheckerIT/.venv/Scripts/python.exe \backend\game\tests\ai\test_mcts.py
C:/Users/JoséManuel/Documents/TFG/CheckerIT/.venv/Scripts/python.exe backend/game/tests/ai/test_comparacion_ias.py
```

## Configuración (opcional) de PostgreSQL

El backend utiliza SQLite por defecto. Para usar PostgreSQL, definir las siguientes variables de entorno:

```env
USE_POSTGRESQL=True
DB_NAME=checkerit_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```



## Reglas de movimiento

Las reglas de movimiento se validan en el backend al registrar movimientos. De forma resumida:

- Movimiento simple: desplazamiento a una casilla adyacente vacía.
- Movimiento por salto: salto colineal sobre una pieza (propia o rival) aterrizando en una casilla vacía.
- Saltos encadenados: posibilidad de concatenar varios saltos consecutivos en la misma ronda con la misma pieza.

## Inteligencia artificial

- Nivel 1: heurística (selección de jugada por evaluación directa).
- Nivel 2 (dificultad “Difícil”): MCTS mediante la librería `imparaai-montecarlo`.
    - La acción que explora el MCTS es una ronda completa sobre una única pieza.
    - Una cadena de saltos se representa como una secuencia y se devuelve como `secuencia`.

## API (resumen)

Base URL: `http://localhost:8000/api/`

Recursos principales (CRUD):

- `/api/jugadores/`
- `/api/partidas/`
- `/api/piezas/`
- `/api/rondas/`
- `/api/movimientos/`
- `/api/participaciones/`
- `/api/agentes-inteligentes/`
- `/api/chatbot/`

Acciones relevantes:

- `POST /api/partidas/start_game/` crea una partida e inicializa jugadores, piezas y ronda.
- `POST /api/partidas/{id_partida}/registrar_movimientos/` registra uno o varios pasos (cadena) de una ronda, validando reglas.
- `POST /api/partidas/{id_partida}/avanzar_ronda/` finaliza la ronda actual y crea la siguiente.
- `POST /api/partidas/{id_partida}/end_game/` finaliza la partida.
- `POST /api/agentes-inteligentes/{id}/sugerir_movimiento/` devuelve una sugerencia de jugada para un agente Inteligente.

## Estructura del proyecto

```text
backend/
    checkerit/              Configuración de Django
    game/                   App principal (modelos, API, validación, agente Inteligente)
    manage.py
    requirements.txt
frontend/
    public/
    src/
        components/
    package.json
```