from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from .models import Jugador, Partida, Pieza, Tablero, Turno, Movimiento, IA, Chatbot, ParticipacionPartida
from .serializers import (
    JugadorSerializer, PartidaSerializer, PartidaListSerializer,
    PiezaSerializer, TableroSerializer, TurnoSerializer, 
    MovimientoSerializer, IASerializer, ChatbotSerializer, ParticipacionPartidaSerializer
)


class JugadorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar jugadores
    """
    queryset = Jugador.objects.all()
    serializer_class = JugadorSerializer


class PartidaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar partidas de Damas Chinas
    """
    queryset = Partida.objects.all()
    serializer_class = PartidaSerializer
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PartidaListSerializer
        return PartidaSerializer
    
    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """
        Crea una nueva partida con jugadores y tablero inicializado
        """
        numero_jugadores = request.data.get('numero_jugadores', 2)
        nombre_jugador1 = request.data.get('nombre_jugador1', 'Jugador 1')
        nombre_jugador2 = request.data.get('nombre_jugador2', 'Jugador 2')
        
        # Crear jugadores
        jugador1 = Jugador.objects.create(
            id_jugador=f"J1_{datetime.now().timestamp()}",
            nombre=nombre_jugador1,
            humano=True
        )
        
        jugador2 = Jugador.objects.create(
            id_jugador=f"J2_{datetime.now().timestamp()}",
            nombre=nombre_jugador2,
            humano=request.data.get('jugador2_ia', False)
        )
        
        # Si jugador 2 es IA, crear configuración de IA
        if not jugador2.humano:
            IA.objects.create(
                jugador=jugador2,
                nivel=request.data.get('nivel_ia', 1)
            )
        
        # Crear partida
        partida = Partida.objects.create(
            id_partida=f"P_{datetime.now().timestamp()}",
            numero_jugadores=numero_jugadores,
            jugador_actual=jugador1
        )
        
        # Crear tablero
        tablero = Tablero.objects.create(
            id_tablero=f"T_{partida.id_partida}",
            dimension="Hexagonal",
            estado_casillas={},
            historial=[]
        )
        
        # Inicializar piezas (ejemplo básico)
        self._initialize_pieces(jugador1, jugador2, partida)
        
        # Crear primer turno
        Turno.objects.create(
            id_turno=f"T1_{partida.id_partida}",
            jugador=jugador1,
            numero=1,
            partida=partida
        )
        
        serializer = self.get_serializer(partida)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def make_move(self, request, pk=None):
        """
        Registra un movimiento en la partida
        """
        partida = self.get_object()
        
        if partida.estado != 'EN_CURSO':
            return Response(
                {'error': 'La partida no está en curso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pieza_id = request.data.get('pieza_id')
        origen = request.data.get('origen')
        destino = request.data.get('destino')
        
        if not all([pieza_id, origen, destino]):
            return Response(
                {'error': 'Datos incompletos para el movimiento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pieza = Pieza.objects.get(id_pieza=pieza_id)
            turno_actual = partida.turnos.filter(fin__isnull=True).first()
            
            if not turno_actual:
                return Response(
                    {'error': 'No hay turno activo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear el movimiento
            movimiento = Movimiento.objects.create(
                id_movimiento=f"M_{datetime.now().timestamp()}",
                jugador=partida.jugador_actual,
                pieza=pieza,
                turno=turno_actual,
                origen=origen,
                destino=destino
            )
            
            # Actualizar posición de la pieza
            pieza.posicion = destino
            pieza.save()
            
            # Finalizar movimiento
            movimiento.fin = timezone.now()
            movimiento.save()
            
            serializer = self.get_serializer(partida)
            return Response(serializer.data)
            
        except Pieza.DoesNotExist:
            return Response(
                {'error': 'Pieza no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def end_turn(self, request, pk=None):
        """
        Finaliza el turno actual y crea el siguiente
        """
        partida = self.get_object()
        turno_actual = partida.turnos.filter(fin__isnull=True).first()
        
        if turno_actual:
            turno_actual.fin = timezone.now()
            turno_actual.save()
            
            # Cambiar jugador actual
            jugadores = Jugador.objects.filter(
                piezas__isnull=False
            ).distinct()[:partida.numero_jugadores]
            
            siguiente_jugador = None
            for i, jugador in enumerate(jugadores):
                if jugador == partida.jugador_actual:
                    siguiente_jugador = jugadores[(i + 1) % len(jugadores)]
                    break
            
            if siguiente_jugador:
                partida.jugador_actual = siguiente_jugador
                partida.save()
                
                # Crear siguiente turno
                Turno.objects.create(
                    id_turno=f"T{turno_actual.numero + 1}_{partida.id_partida}",
                    jugador=siguiente_jugador,
                    numero=turno_actual.numero + 1,
                    partida=partida
                )
        
        serializer = self.get_serializer(partida)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def end_game(self, request, pk=None):
        """
        Finaliza una partida
        """
        partida = self.get_object()
        partida.estado = 'FINALIZADA'
        partida.fecha_fin = timezone.now()
        partida.save()
        
        # Finalizar turno actual si existe
        turno_actual = partida.turnos.filter(fin__isnull=True).first()
        if turno_actual:
            turno_actual.fin = timezone.now()
            turno_actual.save()
        
        serializer = self.get_serializer(partida)
        return Response(serializer.data)
    
    def _initialize_pieces(self, jugador1, jugador2, partida):
        """
        Inicializa las piezas para los jugadores
        """
        # Ejemplo básico - deberás implementar la disposición real de damas chinas
        for i in range(10):
            Pieza.objects.create(
                id_pieza=f"P1_{i}_{partida.id_partida}",
                tipo="Ficha",
                posicion=f"A{i}",
                jugador=jugador1
            )
            
            Pieza.objects.create(
                id_pieza=f"P2_{i}_{partida.id_partida}",
                tipo="Ficha",
                posicion=f"Z{i}",
                jugador=jugador2
            )


class PiezaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar piezas
    """
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer


class TableroViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar tableros
    """
    queryset = Tablero.objects.all()
    serializer_class = TableroSerializer


class TurnoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para turnos
    """
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        partida_id = self.request.query_params.get('partida_id')
        if partida_id:
            queryset = queryset.filter(partida_id=partida_id)
        return queryset


class MovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para movimientos
    """
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        turno_id = self.request.query_params.get('turno_id')
        if turno_id:
            queryset = queryset.filter(turno_id=turno_id)
        return queryset


class IAViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar configuraciones de IA
    """
    queryset = IA.objects.all()
    serializer_class = IASerializer


class ChatbotViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el chatbot
    """
    queryset = Chatbot.objects.all()
    serializer_class = ChatbotSerializer
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Envía un mensaje al chatbot y obtiene respuesta
        """
        chatbot = self.get_object()
        mensaje = request.data.get('mensaje', '')
        
        # Aquí implementarías la lógica del chatbot
        respuesta = f"Respuesta del chatbot a: {mensaje}"
        
        # Actualizar memoria/contexto si es necesario
        if 'conversaciones' not in chatbot.memoria:
            chatbot.memoria['conversaciones'] = []
        
        chatbot.memoria['conversaciones'].append({
            'mensaje': mensaje,
            'respuesta': respuesta,
            'timestamp': str(timezone.now())
        })
        chatbot.save()
        
        return Response({'respuesta': respuesta})


class ParticipacionPartidaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la participación de jugadores en partidas
    """
    queryset = ParticipacionPartida.objects.all()
    serializer_class = ParticipacionPartidaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        partida_id = self.request.query_params.get('partida_id')
        jugador_id = self.request.query_params.get('jugador_id')
        
        if partida_id:
            queryset = queryset.filter(partida_id=partida_id)
        if jugador_id:
            queryset = queryset.filter(jugador_id=jugador_id)
            
        return queryset
