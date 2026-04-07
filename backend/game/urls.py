from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JugadorViewSet, PartidaViewSet, PiezaViewSet,
    RondaViewSet, MovimientoViewSet,
    AgenteInteligenteViewSet, ChatbotViewSet, JugadorPartidaViewSet
)

router = DefaultRouter()
router.register(r'jugadores', JugadorViewSet, basename='jugador')
router.register(r'partidas', PartidaViewSet, basename='partida')
router.register(r'piezas', PiezaViewSet, basename='pieza')
router.register(r'rondas', RondaViewSet, basename='ronda')
router.register(r'movimientos', MovimientoViewSet, basename='movimiento')
router.register(r'agentes-inteligentes', AgenteInteligenteViewSet, basename='agente-inteligente')
router.register(r'chatbot', ChatbotViewSet, basename='chatbot')
router.register(r'participaciones', JugadorPartidaViewSet, basename='participacion')

urlpatterns = [
    path('', include(router.urls)),
]
