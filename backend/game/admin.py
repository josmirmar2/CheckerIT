from django.contrib import admin
from .models import Jugador, Partida, Pieza, Turno, Movimiento, IA, Chatbot, JugadorPartida


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ['id_jugador', 'nombre', 'humano']
    list_filter = ['humano']
    search_fields = ['id_jugador', 'nombre']


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 'numero_jugadores']
    list_filter = ['estado', 'numero_jugadores']
    search_fields = ['id_partida']
    date_hierarchy = 'fecha_inicio'


@admin.register(Pieza)
class PiezaAdmin(admin.ModelAdmin):
    list_display = ['id_pieza', 'tipo', 'posicion', 'jugador', 'chatbot']
    list_filter = ['tipo', 'jugador']
    search_fields = ['id_pieza', 'posicion']


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ['id_turno', 'numero', 'jugador', 'partida', 'inicio', 'fin']
    list_filter = ['jugador', 'partida']
    search_fields = ['id_turno']
    date_hierarchy = 'inicio'


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['id_movimiento', 'jugador', 'pieza', 'turno', 'partida', 'origen', 'destino']
    list_filter = ['jugador', 'partida']
    search_fields = ['id_movimiento', 'origen', 'destino']


@admin.register(IA)
class IAAdmin(admin.ModelAdmin):
    list_display = ['jugador', 'nivel']
    list_filter = ['nivel']


@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    list_display = ['id', 'ia']


@admin.register(JugadorPartida)
class JugadorPartidaAdmin(admin.ModelAdmin):
    list_display = ['jugador', 'partida', 'fecha_union', 'orden_participacion']
    list_filter = ['partida']
    search_fields = ['jugador__nombre']
    date_hierarchy = 'fecha_union'
