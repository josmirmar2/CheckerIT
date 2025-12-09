"""
URL configuration for checkerit project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """Raíz de la API con información de endpoints disponibles"""
    return JsonResponse({
        'mensaje': 'Bienvenido a CheckerIT API',
        'versión': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'api_jugadores': '/api/jugadores/',
            'api_partidas': '/api/partidas/',
            'api_piezas': '/api/piezas/',
            'api_tableros': '/api/tableros/',
            'api_turnos': '/api/turnos/',
            'api_movimientos': '/api/movimientos/',
            'api_ia': '/api/ia/',
            'api_chatbot': '/api/chatbot/',
            'api_participaciones': '/api/participaciones/',
        },
        'documentación': 'Ver /api/ para documentación completa'
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/', include('game.urls')),
]
