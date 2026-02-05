# CheckerIT

CheckerIT es una aplicación web full-stack para jugar a Damas Chinas. El frontend está desarrollado con React y el backend con Django y Django REST Framework.

## Alcance y características principales

- Gestión de partidas: creación, finalización y control de turnos.
- Registro de movimientos con validación de reglas en el backend.
- Interfaz de usuario con tablero, tutorial y pantallas de juego.
- Soporte de jugadores humanos e inteligencia artificial.
- IA con dos niveles: heurística y MCTS (dificultad “Difícil”).

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

### Backend (Django)

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

### Frontend (React)

En una terminal independiente, desde la raíz del proyecto:

```powershell
cd frontend
npm install
npm start
```

El frontend queda disponible en `http://localhost:3000`.

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
- Saltos encadenados: posibilidad de concatenar varios saltos consecutivos en el mismo turno con la misma pieza.

## Inteligencia artificial

- Nivel 1: heurística (selección de jugada por evaluación directa).
- Nivel 2 (dificultad “Difícil”): MCTS mediante la librería `imparaai-montecarlo`.
    - La acción que explora el MCTS es un turno completo sobre una única pieza.
    - Una cadena de saltos se representa como una secuencia y se devuelve como `secuencia`.

## API (resumen)

Base URL: `http://localhost:8000/api/`

Recursos principales (CRUD):

- `/api/jugadores/`
- `/api/partidas/`
- `/api/piezas/`
- `/api/turnos/`
- `/api/movimientos/`
- `/api/participaciones/`
- `/api/ia/`
- `/api/chatbot/`

Acciones relevantes:

- `POST /api/partidas/start_game/` crea una partida e inicializa jugadores, piezas y turno.
- `POST /api/partidas/{id_partida}/registrar_movimientos/` registra uno o varios pasos (cadena) de un turno, validando reglas.
- `POST /api/partidas/{id_partida}/avanzar_turno/` finaliza el turno actual y crea el siguiente.
- `POST /api/partidas/{id_partida}/end_game/` finaliza la partida.
- `POST /api/ia/{id}/sugerir_movimiento/` devuelve una sugerencia de jugada para una IA.

## Estructura del proyecto

```text
backend/
    checkerit/              Configuración de Django
    game/                   App principal (modelos, API, validación, IA)
    manage.py
    requirements.txt
frontend/
    public/
    src/
        components/
    package.json
```