from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from .models import Jugador, Partida, Pieza, Turno, Movimiento, IA, Chatbot, JugadorPartida
from .serializers import (
    JugadorSerializer, PartidaSerializer, PartidaListSerializer,
    PiezaSerializer, TurnoSerializer, 
    MovimientoSerializer, IASerializer, ChatbotSerializer, JugadorPartidaSerializer
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
        Crea una nueva partida con jugadores y piezas inicializadas.
        
        Datos esperados en request:
        {
            "numero_jugadores": 2,
            "jugadores": [
                {"nombre": "Juan", "icono": "icono1.jpg", "tipo": "humano", "dificultad": "Baja"},
                {"nombre": "IA Difícil 2", "icono": "Robot-icon.jpg", "tipo": "ia", "dificultad": "Difícil"}
            ]
        }
        """
        numero_jugadores = request.data.get('numero_jugadores', 2)
        jugadores_data = request.data.get('jugadores', [])
        
        if not jugadores_data or len(jugadores_data) == 0:
            return Response(
                {'error': 'Se requieren datos de jugadores'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        jugadores_list = []
        
        for idx, jugador_data in enumerate(jugadores_data):
            es_humano = jugador_data.get('tipo', 'humano') == 'humano'
            nombre = jugador_data.get('nombre', f'Jugador {idx + 1}')
            
            jugador = Jugador.objects.create(
                id_jugador=f"J{idx + 1}_{datetime.now().timestamp()}",
                nombre=nombre,
                humano=es_humano
            )
            
            if not es_humano:
                dificultad = jugador_data.get('dificultad', 'Fácil')
                nivel = 2 if dificultad == 'Difícil' else 1
                
                IA.objects.create(
                    jugador=jugador,
                    nivel=nivel
                )
            
            jugadores_list.append(jugador)
        
        partida = Partida.objects.create(
            id_partida=f"P_{datetime.now().timestamp()}",
            numero_jugadores=numero_jugadores
        )
        
        for idx, jugador in enumerate(jugadores_list):
            JugadorPartida.objects.create(
                jugador=jugador,
                partida=partida,
                fecha_union=timezone.now(),
                orden_participacion=idx + 1
            )
            self._initialize_pieces(jugador, partida)
        
        Turno.objects.create(
            id_turno=f"T1_{partida.id_partida}",
            jugador=jugadores_list[0],
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
            
            movimiento = Movimiento.objects.create(
                id_movimiento=f"M_{datetime.now().timestamp()}",
                jugador=turno_actual.jugador,
                pieza=pieza,
                turno=turno_actual,
                origen=origen,
                destino=destino
            )
            
            pieza.posicion = destino
            pieza.save()
            
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
            
            jugadores = Jugador.objects.filter(
                piezas__isnull=False
            ).distinct()[:partida.numero_jugadores]

            siguiente_jugador = None
            for i, jugador in enumerate(jugadores):
                if jugador == turno_actual.jugador:
                    siguiente_jugador = jugadores[(i + 1) % len(jugadores)]
                    break

            if siguiente_jugador:
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
        
        turno_actual = partida.turnos.filter(fin__isnull=True).first()
        if turno_actual:
            turno_actual.fin = timezone.now()
            turno_actual.save()
        
        serializer = self.get_serializer(partida)
        return Response(serializer.data)
    
    def _initialize_pieces(self, jugador, partida):
        """
        Inicializa las piezas para los jugadores en sus posiciones iniciales (puntas).
        
        Mapeo de puntas:
        - Punta 0 (Arriba): filas 0-3
        - Punta 1 (Izquierda-Arriba): filas 4-7
        - Punta 2 (Derecha-Arriba): filas 4-7
        - Punta 3 (Abajo): filas 13-16
        - Punta 4 (Izquierda-Abajo): filas 9-12
        - Punta 5 (Derecha-Abajo): filas 9-12
        """
        posiciones_por_punta = {
            0: ['0-0', '1-0', '1-1', '2-0', '2-1', '2-2', '3-0', '3-1', '3-2', '3-3'],
            1: ['0-4', '0-5', '1-4', '1-5', '1-6', '2-4', '2-5', '3-4', '0-6', '0-7'],
            2: ['12-4', '12-5', '11-4', '11-5', '11-6', '10-4', '10-5', '9-4', '12-6', '12-7'],
            3: ['3-13', '2-13', '2-14', '1-13', '1-14', '1-15', '0-13', '0-14', '0-15', '0-16'],
            4: ['0-9', '0-10', '1-9', '1-10', '1-11', '2-10', '2-11', '3-11', '0-11', '0-12'],
            5: ['9-9', '9-10', '10-9', '10-10', '10-11', '11-10', '11-11', '12-11', '9-11', '9-12'],
        }

        colores_por_punta = {
            0: 'Blanco',   
            1: 'Azul', 
            2: 'Verde', 
            3: 'Negro',   
            4: 'Rojo', 
            5: 'Amarillo', 
        }

        participacion = JugadorPartida.objects.get(jugador=jugador, partida=partida)
        punta_index = participacion.orden_participacion - 1
        
        puntas_activas_map = {
            2: [0, 3],
            3: [0, 4, 5],
            4: [1, 2, 4, 5],
            6: [0, 1, 2, 3, 4, 5],
        }
        
        puntas_activas = puntas_activas_map.get(partida.numero_jugadores, [0, 3])
        punta_asignada = puntas_activas[punta_index]
        color_asignado = colores_por_punta.get(punta_asignada, '')
        
        posiciones = posiciones_por_punta.get(punta_asignada, posiciones_por_punta[0])
        
        for i, pos in enumerate(posiciones[:10]): 
            Pieza.objects.create(
                id_pieza=f"P_{jugador.id_jugador}_{i}_{partida.id_partida}",
                tipo=f"{punta_asignada}-{color_asignado}", 
                posicion=pos, 
                jugador=jugador
            )


class PiezaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar piezas
    """
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer

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
        
        respuesta = f"Respuesta del chatbot a: {mensaje}"
        
        if 'conversaciones' not in chatbot.memoria:
            chatbot.memoria['conversaciones'] = []
        
        chatbot.memoria['conversaciones'].append({
            'mensaje': mensaje,
            'respuesta': respuesta,
            'timestamp': str(timezone.now())
        })
        chatbot.save()
        
        return Response({'respuesta': respuesta})


class JugadorPartidaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la participación de jugadores en partidas
    """
    queryset = JugadorPartida.objects.all()
    serializer_class = JugadorPartidaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        partida_id = self.request.query_params.get('partida_id')
        jugador_id = self.request.query_params.get('jugador_id')
        
        if partida_id:
            queryset = queryset.filter(partida_id=partida_id)
        if jugador_id:
            queryset = queryset.filter(jugador_id=jugador_id)
            
        return queryset
