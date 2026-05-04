"""
Django settings for checkerit project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'game',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'checkerit.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'checkerit.wsgi.application'

USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', 'False') == 'True'

if USE_POSTGRESQL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'checkerit_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'client_encoding': 'UTF8',
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

ENFORCE_MOVE_VALIDATION_FOR_HUMANS = os.getenv('ENFORCE_MOVE_VALIDATION_FOR_HUMANS', 'False') == 'True'


GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
GEMINI_API_VERSION = os.getenv('GEMINI_API_VERSION', 'v1')
GEMINI_TIMEOUT_SECONDS = int(os.getenv('GEMINI_TIMEOUT_SECONDS', '15'))
GEMINI_MAX_RETRIES = int(os.getenv('GEMINI_MAX_RETRIES', '2'))
GEMINI_RETRY_BACKOFF_SECONDS = float(os.getenv('GEMINI_RETRY_BACKOFF_SECONDS', '0.6'))

GEMINI_SYSTEM_PROMPT = os.getenv(
    'GEMINI_SYSTEM_PROMPT',
    (
        "Eres un asistente de la aplicación CheckerIT (Damas Chinas). "
        "Responde únicamente sobre: reglas del juego, interfaz, y cómo jugar. "
        "Si te preguntan algo fuera de ese contexto, responde que no puedes ayudar con ese tema. "
        "Cuando te pidan reglas o explicación, responde completo hasta terminar. "
        "Responde en texto plano: no uses Markdown (por ejemplo, no uses **negrita**)."
    ),
)
GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '1024'))
CHATBOT_MAX_INPUT_CHARS = int(os.getenv('CHATBOT_MAX_INPUT_CHARS', '400'))

CHATBOT_DOMAIN_ENFORCE = os.getenv('CHATBOT_DOMAIN_ENFORCE', 'True') == 'True'
CHATBOT_DOMAIN_KEYWORDS = os.getenv('CHATBOT_DOMAIN_KEYWORDS', '')
CHATBOT_REFUSAL_MESSAGE = os.getenv(
    'CHATBOT_REFUSAL_MESSAGE',
    'Solo puedo ayudarte con CheckerIT (reglas del juego e interfaz).',
)
