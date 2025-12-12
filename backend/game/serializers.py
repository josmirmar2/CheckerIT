from rest_framework import serializers
from .models import Jugador, Partida, Pieza, Turno, Movimiento, IA, Chatbot, JugadorPartida


class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = ['id_jugador', 'nombre', 'humano']


class JugadorPartidaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    
    class Meta:
        model = JugadorPartida
        fields = ['id', 'jugador', 'jugador_nombre', 'partida', 'fecha_union', 'orden_participacion']


class PiezaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    
    class Meta:
        model = Pieza
        fields = ['id_pieza', 'tipo', 'posicion', 'jugador', 'jugador_nombre', 'ia', 'chatbot']


class MovimientoSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    pieza_tipo = serializers.CharField(source='pieza.tipo', read_only=True)
    
    class Meta:
        model = Movimiento
        fields = ['id_movimiento', 'jugador', 'jugador_nombre', 'pieza', 'pieza_tipo', 
                  'turno', 'partida', 'origen', 'destino', 'inicio', 'fin']
        read_only_fields = ['inicio']


class TurnoSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Turno
        fields = ['id_turno', 'jugador', 'jugador_nombre', 'numero', 'inicio', 
                  'fin', 'partida', 'movimientos']
        read_only_fields = ['inicio']


class PartidaSerializer(serializers.ModelSerializer):
    turnos = TurnoSerializer(many=True, read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)
    participantes = JugadorPartidaSerializer(source='jugadorpartida_set', many=True, read_only=True)
    
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores', 'turnos', 'movimientos', 'participantes']
        read_only_fields = ['fecha_inicio']


class PartidaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores']
        read_only_fields = ['fecha_inicio']


class IASerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    
    class Meta:
        model = IA
        fields = ['jugador', 'jugador_nombre', 'nivel']


class ChatbotSerializer(serializers.ModelSerializer):
    ia_jugador = serializers.CharField(source='ia.jugador.nombre', read_only=True)
    
    class Meta:
        model = Chatbot
        fields = ['id', 'ia', 'ia_jugador', 'memoria', 'contexto']
