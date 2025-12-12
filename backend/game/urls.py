from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JugadorViewSet, PartidaViewSet, PiezaViewSet,
    TurnoViewSet, MovimientoViewSet,
    IAViewSet, ChatbotViewSet, JugadorPartidaViewSet
)

router = DefaultRouter()
router.register(r'jugadores', JugadorViewSet, basename='jugador')
router.register(r'partidas', PartidaViewSet, basename='partida')
router.register(r'piezas', PiezaViewSet, basename='pieza')
router.register(r'turnos', TurnoViewSet, basename='turno')
router.register(r'movimientos', MovimientoViewSet, basename='movimiento')
router.register(r'ia', IAViewSet, basename='ia')
router.register(r'chatbot', ChatbotViewSet, basename='chatbot')
router.register(r'participaciones', JugadorPartidaViewSet, basename='participacion')

urlpatterns = [
    path('', include(router.urls)),
]
