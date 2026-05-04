from rest_framework import serializers
from .models import (
    Jugador,
    Partida,
    Pieza,
    Ronda,
    Movimiento,
    AgenteInteligente,
    Chatbot,
    JugadorPartida,
    is_valid_position_key,
)


class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = ['id_jugador', 'nombre', 'humano', 'numero']


class JugadorPartidaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)

    def validate(self, attrs):
        partida = attrs.get('partida')
        jugador = attrs.get('jugador')
        orden = attrs.get('orden_participacion')

        if partida is not None:
            limit = getattr(partida, 'numero_jugadores', None) or 6
            qs = JugadorPartida.objects.filter(partida=partida)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.count() >= limit:
                raise serializers.ValidationError({'partida': f'Una partida no puede tener más de {limit} jugadores'})

            if orden is not None:
                try:
                    orden_int = int(orden)
                except Exception:
                    raise serializers.ValidationError({'orden_participacion': 'orden_participacion debe ser un entero'})

                if orden_int < 1 or orden_int > limit:
                    raise serializers.ValidationError({'orden_participacion': f'orden_participacion debe estar entre 1 y {limit}'})

                existing_orden = JugadorPartida.objects.filter(partida=partida, orden_participacion=orden_int)
                if self.instance is not None:
                    existing_orden = existing_orden.exclude(pk=self.instance.pk)
                if existing_orden.exists():
                    raise serializers.ValidationError({'orden_participacion': 'Ese orden_participacion ya está ocupado en la partida'})

        if partida is not None and jugador is not None:
            existing_pair = JugadorPartida.objects.filter(partida=partida, jugador=jugador)
            if self.instance is not None:
                existing_pair = existing_pair.exclude(pk=self.instance.pk)
            if existing_pair.exists():
                raise serializers.ValidationError({'jugador': 'El jugador ya está inscrito en esta partida'})

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

    def validate_posicion(self, value):
        if not is_valid_position_key(str(value)):
            raise serializers.ValidationError('Posición inválida: fuera del tablero')
        return value
    
    class Meta:
        model = Pieza
        fields = ['id_pieza', 'tipo', 'posicion', 'jugador', 'jugador_nombre', 'chatbot', 'partida']


class MovimientoSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    pieza_tipo = serializers.CharField(source='pieza.tipo', read_only=True)

    def validate_origen(self, value):
        if not is_valid_position_key(str(value)):
            raise serializers.ValidationError('Posición inválida: fuera del tablero')
        return value

    def validate_destino(self, value):
        if not is_valid_position_key(str(value)):
            raise serializers.ValidationError('Posición inválida: fuera del tablero')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        pieza = attrs.get('pieza') if 'pieza' in attrs else getattr(self.instance, 'pieza', None)
        origen = attrs.get('origen') if 'origen' in attrs else getattr(self.instance, 'origen', None)
        destino = attrs.get('destino') if 'destino' in attrs else getattr(self.instance, 'destino', None)
        ronda = attrs.get('ronda') if 'ronda' in attrs else getattr(self.instance, 'ronda', None)
        partida = attrs.get('partida') if 'partida' in attrs else getattr(self.instance, 'partida', None)

        if pieza is not None and origen is not None:
            if str(origen) != str(pieza.posicion):
                raise serializers.ValidationError({
                    'origen': 'El origen debe coincidir con la posición actual de la pieza'
                })

        partida_ctx = None
        if ronda is not None:
            partida_ctx = ronda.partida
        if partida_ctx is None:
            partida_ctx = partida
        if partida_ctx is None and pieza is not None:
            partida_ctx = pieza.partida

        if partida_ctx is not None and destino is not None and pieza is not None:
            if Pieza.objects.filter(partida=partida_ctx, posicion=str(destino)).exclude(pk=pieza.pk).exists():
                raise serializers.ValidationError({'destino': 'El destino está ocupado por otra pieza'})

        return attrs
    
    class Meta:
        model = Movimiento
        fields = ['id_movimiento', 'jugador', 'jugador_nombre', 'pieza', 'pieza_tipo', 
                  'ronda', 'partida', 'origen', 'destino']


class RondaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ronda
        fields = ['id_ronda', 'jugador', 'jugador_nombre', 'numero', 'inicio', 
                  'fin', 'partida', 'movimientos']
        read_only_fields = ['inicio']


class PartidaSerializer(serializers.ModelSerializer):
    rondas = RondaSerializer(many=True, read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)
    participantes = JugadorPartidaSerializer(source='jugadorpartida_set', many=True, read_only=True)
    
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores', 'tiempo_sobrante', 'is_demo', 'rondas', 'movimientos', 'participantes']
        read_only_fields = ['fecha_inicio']


class PartidaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        fields = ['id_partida', 'fecha_inicio', 'fecha_fin', 'estado', 
                  'numero_jugadores', 'tiempo_sobrante', 'is_demo']
        read_only_fields = ['fecha_inicio']


class AgenteInteligenteSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    
    class Meta:
        model = AgenteInteligente
        fields = ['jugador', 'jugador_nombre', 'nivel']


class ChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chatbot
        fields = ['id', 'partida', 'jugador', 'memoria']
