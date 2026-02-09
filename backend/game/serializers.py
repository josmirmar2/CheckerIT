from rest_framework import serializers
from .models import Jugador, Partida, Pieza, Turno, Movimiento, IA, Chatbot, JugadorPartida


class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = ['id_jugador', 'nombre', 'humano', 'numero']


class JugadorPartidaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)

    def validate(self, attrs):
        partida = attrs.get('partida')
        jugador = attrs.get('jugador')

        if partida is not None:
            # Máximo 6 jugadores por partida
            qs = JugadorPartida.objects.filter(partida=partida)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.count() >= 6:
                raise serializers.ValidationError({'partida': 'Una partida no puede tener más de 6 jugadores'})

        if partida is not None and jugador is not None:
            # Evitar duplicar el numero de jugador dentro de la misma partida.
            numero = getattr(jugador, 'numero', None)
            if numero is not None:
                existing = JugadorPartida.objects.filter(partida=partida, jugador__numero=numero)
                if self.instance is not None:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise serializers.ValidationError({'jugador': f'Ya existe un jugador con numero={numero} en esta partida'})

        return attrs
    
    class Meta:
        model = JugadorPartida
        fields = ['id', 'jugador', 'jugador_nombre', 'partida', 'fecha_union', 'orden_participacion']


class PiezaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    
    class Meta:
        model = Pieza
        fields = ['id_pieza', 'tipo', 'posicion', 'jugador', 'jugador_nombre', 'ia', 'chatbot', 'partida']


class MovimientoSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    pieza_tipo = serializers.CharField(source='pieza.tipo', read_only=True)
    
    class Meta:
        model = Movimiento
        fields = ['id_movimiento', 'jugador', 'jugador_nombre', 'pieza', 'pieza_tipo', 
                  'turno', 'partida', 'origen', 'destino']


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
                  'numero_jugadores', 'tiempo_sobrante', 'turnos', 'movimientos', 'participantes']
        read_only_fields = ['fecha_inicio']


class PartidaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores', 'tiempo_sobrante']
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
