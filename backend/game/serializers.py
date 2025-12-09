from rest_framework import serializers
from .models import Jugador, Partida, Pieza, Tablero, Turno, Movimiento, IA, Chatbot, ParticipacionPartida


class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = ['id_jugador', 'nombre', 'humano']


class ParticipacionPartidaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    
    class Meta:
        model = ParticipacionPartida
        fields = ['id', 'jugador', 'jugador_nombre', 'partida', 'fecha_union', 'orden_participacion']


class PiezaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    tablero_id = serializers.CharField(source='tablero.id_tablero', read_only=True)
    
    class Meta:
        model = Pieza
        fields = ['id_pieza', 'tipo', 'posicion', 'jugador', 'jugador_nombre', 'tablero', 'tablero_id']


class TableroSerializer(serializers.ModelSerializer):
    piezas = PiezaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Tablero
        fields = ['id_tablero', 'dimension', 'estado_casillas', 'historial', 'piezas']


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
    jugador_actual_nombre = serializers.CharField(source='jugador_actual.nombre', read_only=True)
    turnos = TurnoSerializer(many=True, read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)
    participantes = ParticipacionPartidaSerializer(source='participacionpartida_set', many=True, read_only=True)
    
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores', 'jugador_actual', 'jugador_actual_nombre', 
                  'tablero', 'turnos', 'movimientos', 'participantes']
        read_only_fields = ['fecha_inicio']


class PartidaListSerializer(serializers.ModelSerializer):
    jugador_actual_nombre = serializers.CharField(source='jugador_actual.nombre', read_only=True)
    
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores', 'jugador_actual', 'jugador_actual_nombre']
        read_only_fields = ['fecha_inicio']


class IASerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    tablero_id = serializers.CharField(source='tablero.id_tablero', read_only=True)
    
    class Meta:
        model = IA
        fields = ['jugador', 'jugador_nombre', 'nivel', 'tablero', 'tablero_id']


class ChatbotSerializer(serializers.ModelSerializer):
    ia_jugador = serializers.CharField(source='ia.jugador.nombre', read_only=True)
    tablero_id = serializers.CharField(source='tablero.id_tablero', read_only=True)
    
    class Meta:
        model = Chatbot
        fields = ['id', 'ia', 'ia_jugador', 'tablero', 'tablero_id', 'memoria', 'contexto']
