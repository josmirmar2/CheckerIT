# CheckerIT - Juego de Damas Chinas

Aplicación web full-stack para jugar a las Damas Chinas, desarrollada con React (frontend) y Django (backend) con base de datos PostgreSQL.

## 🎮 Características

- Pantalla de inicio con opciones de Tutorial y Empezar Partida
- Sistema de juego de Damas Chinas para 2 jugadores
- Tutorial interactivo con reglas del juego
- API REST para gestión de partidas y movimientos
- Interfaz moderna y responsiva

## 🛠️ Tecnologías

### Frontend
- React 18
- React Router DOM
- Axios
- CSS3

### Backend
- Django 5.0
- Django REST Framework
- PostgreSQL
- CORS Headers

## 📋 Requisitos Previos

- Node.js (v14 o superior)
- Python 3.8 o superior
- PostgreSQL 12 o superior
- npm o yarn

## 🚀 Instalación

### Opción rápida (VS Code): ejecutar todo de una vez

Si estás usando VS Code, puedes levantar backend + frontend sin teclear los comandos uno a uno:

- Abre la paleta de comandos: `Ctrl+Shift+P`
- Ejecuta: **Tasks: Run Task**
- Selecciona: **Dev: iniciar (backend+frontend)**

Esto crea el `venv` si no existe, instala dependencias, aplica migraciones y arranca ambos servidores.

### Opción rápida (PowerShell): un script

Desde la raíz del proyecto:

```powershell
.\scripts\dev.ps1
```

Por defecto abre ventanas de PowerShell con los logs (backend y frontend). Opcionalmente:

```powershell
# Abrir el navegador automáticamente
.\scripts\dev.ps1 -OpenBrowser

# Solo backend o solo frontend
.\scripts\dev.ps1 -BackendOnly
.\scripts\dev.ps1 -FrontendOnly

# Lanzar en segundo plano (sin ventanas/logs)
.\scripts\dev.ps1 -Mode background
```

Si PowerShell te bloquea scripts por permisos:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\dev.ps1
```

### 1. Configurar la Base de Datos

Primero, crea la base de datos PostgreSQL:

```sql
CREATE DATABASE checkerit_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE checkerit_db TO postgres;
```

### 2. Configurar el Backend (Django)

```powershell
# Navegar a la carpeta backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de configuración
copy .env.example .env

# Editar .env con tus credenciales de PostgreSQL

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Iniciar servidor de desarrollo
python manage.py runserver
```

El backend estará disponible en: `http://localhost:8000`

### 3. Configurar el Frontend (React)

```powershell
# Abrir una nueva terminal y navegar a la carpeta frontend
cd frontend

# Instalar dependencias
npm install

# Copiar archivo de configuración
copy .env.example .env

# Iniciar servidor de desarrollo
npm start
```

El frontend estará disponible en: `http://localhost:3000`

## 📁 Estructura del Proyecto

```
TFG/
├── backend/
│   ├── checkerit/          # Configuración del proyecto Django
│   │   ├── settings.py     # Configuración principal
│   │   ├── urls.py         # URLs principales
│   │   └── ...
│   ├── game/               # App del juego
│   │   ├── models.py       # Modelos de Game y Move
│   │   ├── views.py        # ViewSets para la API
│   │   ├── serializers.py  # Serializadores
│   │   ├── urls.py         # URLs de la app
│   │   └── admin.py        # Configuración del admin
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── components/
    │   │   ├── Home.js         # Pantalla de inicio
    │   │   ├── Game.js         # Componente del juego
    │   │   ├── Tutorial.js     # Tutorial del juego
    │   │   └── *.css          # Estilos
    │   ├── App.js
    │   ├── index.js
    │   └── ...
    ├── package.json
    └── .env.example
```

## 🎯 API Endpoints

### Juegos (Games)

- `GET /api/games/` - Listar todas las partidas
- `POST /api/games/` - Crear una partida
- `GET /api/games/{id}/` - Obtener detalles de una partida
- `POST /api/games/start_game/` - Iniciar nueva partida
- `POST /api/games/{id}/make_move/` - Realizar un movimiento
- `POST /api/games/{id}/end_game/` - Finalizar partida

### Movimientos (Moves)

- `GET /api/moves/` - Listar movimientos
- `GET /api/moves/?game_id={id}` - Movimientos de una partida específica

## 🎲 Modelos de Datos

### Game (Partida)
- `id`: ID único
- `status`: Estado (waiting, in_progress, finished)
- `current_player`: Jugador actual (1 o 2)
- `board_state`: Estado del tablero (JSON)
- `winner`: Ganador (opcional)
- `created_at`: Fecha de creación
- `updated_at`: Última actualización

### Move (Movimiento)
- `id`: ID único
- `game`: Relación con la partida
- `player`: Jugador que realizó el movimiento
- `from_position`: Posición inicial (JSON)
- `to_position`: Posición final (JSON)
- `created_at`: Fecha del movimiento

## 🔧 Configuración

### Variables de Entorno - Backend (.env)

```env
DB_NAME=checkerit_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=tu_clave_secreta_django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Variables de Entorno - Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000/api
```

## Solución de Problemas

### Error de conexión a PostgreSQL
- Verifica que PostgreSQL esté ejecutándose
- Comprueba las credenciales en el archivo `.env`
- Asegúrate de que la base de datos existe

### Error de CORS
- Verifica que el backend esté corriendo en el puerto 8000
- Comprueba la configuración de CORS_ALLOWED_ORIGINS en settings.py

### Errores de npm
- Elimina la carpeta `node_modules` y ejecuta `npm install` de nuevo
- Limpia el cache con `npm cache clean --force`

## Notas de Desarrollo

- No incluye sistema de autenticación (según especificaciones)
- La lógica del tablero está preparada para ser implementada en `views.py`
- El estado del tablero se guarda en formato JSON en PostgreSQL

## Contribuir

Este es un proyecto académico (TFG). 

## Licencia

Este proyecto es un Trabajo Fin de Grado (TFG).

---

Desarrollado con ❤️ para el TFG