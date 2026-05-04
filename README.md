# CheckerIT

CheckerIT es una aplicación web full-stack para jugar a Damas Chinas. El frontend está desarrollado con React y el backend con Django y Django REST Framework.

## Objetivos principales

- Creación de una aplicación que tenga integrado un videojuego basado en el juego de mesa Damas Chinas
- Implementación de un tutorial de entrenamiento del juego de mesa Damas Chinas.
- Creación de un agente inteligente que permita simular un jugador basado en la metodología Heurística de asignación de valor.
- Integración del agente inteligente Monte Carlo Tree Search.
- Creación e implementación de un chatbot capaz de proporcionar ayuda y un tutorial al usuario si lo necesita.

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

### Testing de Seguridad: Hacking y Anti-Tampering

#### Backend: Tests de Hacking

Se han añadido tests de penetración en el backend para validar que la API rechaza intentos de manipulación de estado del juego:

**Test de Movimientos (`backend/game/tests/integration/test_api_movimientos.py`):**
- `test_registrar_movimientos_falla_si_jugador_no_existe` — Rechaza jugador_id inexistente
- `test_registrar_movimientos_falla_si_ronda_no_existe` — Rechaza cuando no hay ronda activa
- `test_registrar_movimientos_falla_si_pieza_no_existe` — Rechaza pieza_id inexistente
- `test_registrar_movimientos_falla_si_destino_fuera_del_tablero` — Rechaza posiciones fuera del tablero

**Test de Anti-Tampering en Rondas (`backend/game/tests/integration/test_api_partidas.py`):**
- `test_accion_avanzar_ronda_rechaza_jugador_no_esperado` — Rechaza si jugador_id no coincide con el esperado en la secuencia de participantes
- `test_accion_avanzar_ronda_rechaza_numero_tampered` — Rechaza si el número de ronda no es secuencial (e.g., intentar numero=99 en lugar de numero=2)
- `test_accion_avanzar_ronda_rechaza_jugador_fuera_de_partida` — Rechaza si el jugador no está registrado en la partida
- `test_accion_avanzar_ronda_rechaza_old_round_de_otra_partida` — Rechaza si el oldRound pertenece a una partida diferente

**Ejecutar tests:**

```powershell
cd backend
python -m pytest game/tests/integration/test_api_movimientos.py -v
python -m pytest game/tests/integration/test_api_partidas.py -v
```

#### Frontend: Guards de Integridad

Se ha implementado un módulo de validación cliente-side en `frontend/src/security/integrityGuards.js` que previene el envío de payloads tamperizados al backend:

**Tests Frontend (`frontend/src/security/integrityGuards.test.js`):**

```powershell
cd frontend
npm run test -- --watchAll=false --runInBand
```

### Cobertura de Testing

- **Backend**: 139 tests pasando 
- **Frontend**: 4 tests pasando (integrityGuards.test.js)
- **Total Warnings**: 4 warnings en backend, no relacionadas con seguridad

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

## Chatbot (Gemini)

El chatbot se ejecuta en el backend (Django) y llama a Gemini usando una API key guardada en variables de entorno.

En `backend/.env` añade:

```env
GEMINI_API_KEY=tu_api_key_de_gemini
# Opcional: si no lo defines, el backend intentará auto-seleccionar un modelo compatible.
GEMINI_MODEL=
# Opcional: 'v1' (recomendado) o 'v1beta'
GEMINI_API_VERSION=v1

# Opcional: reintentos cuando Gemini esté saturado (503) o limitado (429)
GEMINI_MAX_RETRIES=2
GEMINI_RETRY_BACKOFF_SECONDS=0.6

# Opcional: hacer el chatbot más restrictivo
GEMINI_SYSTEM_PROMPT=Eres un asistente de CheckerIT; responde solo sobre reglas e interfaz.
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_OUTPUT_TOKENS=256
CHATBOT_MAX_INPUT_CHARS=400

# Hard gate (rechaza fuera de dominio sin llamar a Gemini)
CHATBOT_DOMAIN_ENFORCE=True
# Si lo dejas vacío, usa una lista por defecto.
CHATBOT_DOMAIN_KEYWORDS=checkerit,reglas,tablero,pieza,movimiento,turno,interfaz
CHATBOT_REFUSAL_MESSAGE=Solo puedo ayudarte con CheckerIT (reglas del juego e interfaz).
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

## API 

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
    game/                   App principal (modelos, API, validación, agente inteligente)
    manage.py
    requirements.txt
frontend/
    public/
    src/
        components/
    package.json
```