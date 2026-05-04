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
python -m pytest game/tests/integration/test_api_partidas.py::TestAccionesPartida::test_accion_avanzar_ronda -v
```

#### Frontend: Guards de Integridad

Se ha implementado un módulo de validación cliente-side en `frontend/src/security/integrityGuards.js` que previene el envío de payloads tamperizados al backend:

**Funciones principales:**

1. `isValidPositionKey(key)` — Valida formato de posición (col-fila) contra las dimensiones del tablero hexagonal
2. `buildSecureMovimientosPayload({moveHistory, actualRound, dbJugadores, currentPlayerIndex, partida})` — Filtra y sanitiza movimientos:
   - Valida posiciones válidas (origen y destino)
   - Asegura que pieza_id está presente
   - Filtra movimientos donde origen == destino
   - Valida campos completos requeridos
3. `buildRoundAdvancePayload({partidaId, actualRound, dbJugadores, currentPlayerIndex})` — Construye el payload de avance de ronda:
   - Calcula el siguiente jugador según la secuencia circular de participantes
   - Incremente monotónico del número de ronda (numero + 1)
   - Retorna objeto con oldRound y newRoundCreated, o null si hay campos faltantes

**Tests Frontend (`frontend/src/security/integrityGuards.test.js`):**

```powershell
cd frontend
npm run test -- --watchAll=false --runInBand
```

#### Arquitectura de Seguridad: Defense in Depth

CheckerIT implementa validación en múltiples capas:

```
Cliente (React)
  ↓
  ├─ Guard de Integridad: isValidPositionKey, buildSecureMov...Payload
  │  └─ Filtra movimientos/rondas tamperizados antes de red
  ↓
Backend (Django REST)
  ├─ Validación Autoritativa: avanzar_ronda
  │  ├─ Valida jugador esperado (JugadorPartida.orden_participacion)
  │  ├─ Rechaza número de ronda no secuencial
  │  ├─ Rechaza oldRound de partida distinta
  │  └─ Rechaza jugador no inscrito
  ├─ Validación de Movimientos: registrar_movimientos
  │  ├─ Valida pieza_id existe y pertenece a jugador
  │  ├─ Valida posición dentro de tablero (ROW_LENGTHS)
  │  ├─ Rechaza DoesNotExist para jugador/ronda/pieza
  │  └─ Valida reglas (movimiento simple vs. salto)
  ↓
Base de Datos
  └─ Constraints: unique, foreign key, check
```

**Principios de Defensa:**
- Server-Authoritative: El servidor nunca confía en datos del cliente; re-valida todo
- Monotonic Progression: Números de ronda estrictamente secuenciales previenen ID collisions
- Public Code Defense: Los guards cliente-side asumen que el atacante tiene acceso al código fuente
- DoesNotExist Fast-Path: Validación temprana de entidades inexistentes reduce carga

## Cambios Implementados en Esta Iteración

### Backend: Hardening de `avanzar_ronda` (`backend/game/views.py`)

Se ha reforzado el método `avanzar_ronda` (líneas 672-830) con validaciones anti-tampering:

- **Validación de Jugador Esperado**: Verifica que `jugador_id` coincida con el siguiente jugador en `JugadorPartida.orden_participacion`, evitando que un jugador suplante otro
- **Número de Ronda Secuencial**: Rechaza cualquier `numero` que no sea exactamente `actual_round.numero + 1`, previniendo:
  - Saltos de ronda
  - Reutilización de números (ID collisions)
  - Replay attacks
- **Validación de Partida**: Rechaza `oldRound` que pertenezca a una partida distinta
- **Membresía en Partida**: Rechaza `jugador_id` no inscrito en la partida

**Cambios en Tests**: Se actualizó `test_accion_avanzar_ronda_crea_nueva_ronda` para usar `numero=2` en lugar de `numero=1` (ahora hay ronda 1 inicial, así que el avance debe ser a ronda 2).

### Frontend: Módulo de Guards de Integridad (NUEVO)

**Archivo creado**: `frontend/src/security/integrityGuards.js`

Módulo de funciones puras que sanitizan payloads antes de enviarlos al backend:

```javascript
export function isValidPositionKey(key) { /* col-fila validation */ }
export function buildSecureMovimientosPayload({moveHistory, actualRound, dbJugadores, currentPlayerIndex, partida}) { /* move filtering */ }
export function buildRoundAdvancePayload({partidaId, actualRound, dbJugadores, currentPlayerIndex}) { /* round advancement */ }
```

**Beneficios:**
- Evita enviar movimientos/rondas obviamente tamperizadas
- Reduce carga en servidor (validación temprana)
- Proporciona mejor UX (feedback cliente-side rápido)
- Asume que el atacante tiene acceso al código (defense in depth)

**Archivo de Tests**: `frontend/src/security/integrityGuards.test.js` (4 tests, todos pasando)

### Frontend: Integración de Guards en `Game.js`

Se ha integrado los guards en el flujo principal de `frontend/src/components/Game.js`:

- `saveMoveToDatabase()`: Ahora llama a `buildSecureMovimientosPayload()` para filtrar moveHistory antes de registrar en servidor
- `saveRoundToDatabase()`: Ahora llama a `buildRoundAdvancePayload()` para construir el payload de ronda en lugar de lógica ad-hoc

**Impacto**: El cliente ahora rechaza movimientos obviamente inválidos antes de la red, manteniendo seguridad servidor-autoritativa.

### Cobertura de Testing

- **Backend**: 139 tests pasando (incluyendo 11 nuevos tests de hacking/anti-tampering)
- **Frontend**: 4 tests pasando (integrityGuards.test.js)
- **Total Warnings**: 4 warnings en backend (deprecaciones normales, no relacionadas con seguridad)

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

Endpoint:

- `POST /api/chatbot/send_message/` con body JSON `{ "mensaje": "...", "chatbot_id": 1 }`.
    - `chatbot_id` es opcional: si no lo envías, el backend usará/creará uno.



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