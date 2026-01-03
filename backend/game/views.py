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

CARTESIAN_COORD_ROWS = [
    [{"q": 0, "r": 0}],
    [{"q": -1, "r": 1}, {"q": 0, "r": 1}],
    [{"q": -2, "r": 2}, {"q": -1, "r": 2}, {"q": 0, "r": 2}],
    [{"q": -3, "r": 3}, {"q": -2, "r": 3}, {"q": -1, "r": 3}, {"q": 0, "r": 3}],
    [{"q": -8, "r": 4}, {"q": -7, "r": 4}, {"q": -6, "r": 4}, {"q": -5, "r": 4}, {"q": -4, "r": 4}, {"q": -3, "r": 4}, {"q": -2, "r": 4}, {"q": -1, "r": 4}, {"q": 0, "r": 4}, {"q": 1, "r": 4}, {"q": 2, "r": 4}, {"q": 3, "r": 4}, {"q": 4, "r": 4}],
    [{"q": -8, "r": 5}, {"q": -7, "r": 5}, {"q": -6, "r": 5}, {"q": -5, "r": 5}, {"q": -4, "r": 5}, {"q": -3, "r": 5}, {"q": -2, "r": 5}, {"q": -1, "r": 5}, {"q": 0, "r": 5}, {"q": 1, "r": 5}, {"q": 2, "r": 5}, {"q": 3, "r": 5}],
    [{"q": -8, "r": 6}, {"q": -7, "r": 6}, {"q": -6, "r": 6}, {"q": -5, "r": 6}, {"q": -4, "r": 6}, {"q": -3, "r": 6}, {"q": -2, "r": 6}, {"q": -1, "r": 6}, {"q": 0, "r": 6}, {"q": 1, "r": 6}, {"q": 2, "r": 6}],
    [{"q": -8, "r": 7}, {"q": -7, "r": 7}, {"q": -6, "r": 7}, {"q": -5, "r": 7}, {"q": -4, "r": 7}, {"q": -3, "r": 7}, {"q": -2, "r": 7}, {"q": -1, "r": 7}, {"q": 0, "r": 7}, {"q": 1, "r": 7}],
    [{"q": -8, "r": 8}, {"q": -7, "r": 8}, {"q": -6, "r": 8}, {"q": -5, "r": 8}, {"q": -4, "r": 8}, {"q": -3, "r": 8}, {"q": -2, "r": 8}, {"q": -1, "r": 8}, {"q": 0, "r": 8}],
    [{"q": -9, "r": 9}, {"q": -8, "r": 9}, {"q": -7, "r": 9}, {"q": -6, "r": 9}, {"q": -5, "r": 9}, {"q": -4, "r": 9}, {"q": -3, "r": 9}, {"q": -2, "r": 9}, {"q": -1, "r": 9}, {"q": 0, "r": 9}],
    [{"q": -10, "r": 10}, {"q": -9, "r": 10}, {"q": -8, "r": 10}, {"q": -7, "r": 10}, {"q": -6, "r": 10}, {"q": -5, "r": 10}, {"q": -4, "r": 10}, {"q": -3, "r": 10}, {"q": -2, "r": 10}, {"q": -1, "r": 10}, {"q": 0, "r": 10}],
    [{"q": -11, "r": 11}, {"q": -10, "r": 11}, {"q": -9, "r": 11}, {"q": -8, "r": 11}, {"q": -7, "r": 11}, {"q": -6, "r": 11}, {"q": -5, "r": 11}, {"q": -4, "r": 11}, {"q": -3, "r": 11}, {"q": -2, "r": 11}, {"q": -1, "r": 11}, {"q": 0, "r": 11}],
    [{"q": -12, "r": 12}, {"q": -11, "r": 12}, {"q": -10, "r": 12}, {"q": -9, "r": 12}, {"q": -8, "r": 12}, {"q": -7, "r": 12}, {"q": -6, "r": 12}, {"q": -5, "r": 12}, {"q": -4, "r": 12}, {"q": -3, "r": 12}, {"q": -2, "r": 12}, {"q": -1, "r": 12}, {"q": 0, "r": 12}],
    [{"q": -8, "r": 13}, {"q": -7, "r": 13}, {"q": -6, "r": 13}, {"q": -5, "r": 13}],
    [{"q": -8, "r": 14}, {"q": -7, "r": 14}, {"q": -6, "r": 14}],
    [{"q": -8, "r": 15}, {"q": -7, "r": 15}],
    [{"q": -8, "r": 16}],
]

POSITION_TO_CARTESIAN = {}
CARTESIAN_TO_POSITION = {}
for fila_idx, row in enumerate(CARTESIAN_COORD_ROWS):
    for col_idx, coord in enumerate(row):
        key = f"{col_idx}-{fila_idx}"
        POSITION_TO_CARTESIAN[key] = coord
        CARTESIAN_TO_POSITION[f"{coord['q']},{coord['r']}"] = key

AXIAL_DIRECTIONS = [
    {"dq": 1, "dr": 0},
    {"dq": -1, "dr": 0},
    {"dq": 0, "dr": 1},
    {"dq": 0, "dr": -1},
    {"dq": 1, "dr": -1},
    {"dq": -1, "dr": 1},
]


def get_occupied_positions(partida_id):
    """Obtiene todas las posiciones ocupadas en una partida."""
    piezas = Pieza.objects.filter(partida_id=partida_id)
    return {pieza.posicion for pieza in piezas if pieza.posicion}


def coord_from_key(key):
    """Convierte posición col-fila a coordenadas axiales."""
    return POSITION_TO_CARTESIAN.get(key)


def key_from_coord(q, r):
    """Convierte coordenadas axiales a posición col-fila."""
    return CARTESIAN_TO_POSITION.get(f"{q},{r}")


def compute_simple_moves(origin_key, occupied_positions):
    """Calcula movimientos simples (vecinos vacíos)."""
    origin_coord = coord_from_key(origin_key)
    if not origin_coord:
        return []
    
    moves = []
    for direction in AXIAL_DIRECTIONS:
        neighbor_q = origin_coord["q"] + direction["dq"]
        neighbor_r = origin_coord["r"] + direction["dr"]
        neighbor_key = key_from_coord(neighbor_q, neighbor_r)
        
        if neighbor_key and neighbor_key not in occupied_positions:
            moves.append(neighbor_key)
    
    return moves


def compute_jump_moves(origin_key, occupied_positions):
    """Calcula saltos con encadenamiento (DFS)."""
    origin_coord = coord_from_key(origin_key)
    if not origin_coord:
        return []
    
    landings = set()
    
    def dfs(coord):
        for direction in AXIAL_DIRECTIONS:
            middle_q = coord["q"] + direction["dq"]
            middle_r = coord["r"] + direction["dr"]
            landing_q = coord["q"] + 2 * direction["dq"]
            landing_r = coord["r"] + 2 * direction["dr"]
            
            middle_key = key_from_coord(middle_q, middle_r)
            landing_key = key_from_coord(landing_q, landing_r)
            
            if not middle_key or not landing_key:
                continue
            if middle_key not in occupied_positions: 
                continue
            if landing_key in occupied_positions:
                continue
            
            if landing_key not in landings:
                landings.add(landing_key)
                dfs({"q": landing_q, "r": landing_r})
    
    dfs(origin_coord)
    return list(landings)


def get_valid_moves_from(origin_key, occupied_positions, allow_simple=True):
    """Obtiene todos los movimientos válidos desde una posición."""
    simple = compute_simple_moves(origin_key, occupied_positions) if allow_simple else []
    jumps = compute_jump_moves(origin_key, occupied_positions)
    return list(set(simple + jumps))


def validate_move(origin_key, destination_key, occupied_positions, allow_simple=True):
    """
    Valida si un movimiento de origen a destino es válido.
    Retorna (es_válido: bool, mensaje_error: str)
    VALIDACIONES DESHABILITADAS - Acepta cualquier movimiento
    """
    # Validaciones deshabilitadas - acepta todos los movimientos
    return True, ""




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
    lookup_field = 'id_partida'
    lookup_value_regex = '[^/]+'
    
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
            numero = jugador_data.get('numero', idx + 1)
            
            jugador = Jugador.objects.create(
                id_jugador=f"J{idx + 1}_{datetime.now().timestamp()}",
                nombre=nombre,
                humano=es_humano,
                numero=numero
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
    def actualizar_posiciones_iniciales(self, request, id_partida=None):
        """
        Actualiza las posiciones de todas las piezas de la partida a sus posiciones iniciales
        según la punta asignada a cada jugador.
        """
        partida = self.get_object()
        
        posiciones_por_punta = {
            0: ['0-0', '0-1', '1-1', '0-2', '1-2', '2-2', '0-3', '1-3', '2-3', '3-3'],
            1: ['0-4', '0-5', '1-4', '1-5', '1-6', '2-4', '2-5', '3-4', '0-6', '0-7'],
            2: ['12-4', '9-6', '11-4', '11-5', '10-6', '10-4', '10-5', '9-5', '9-4', '9-7'],
            3: ['3-13', '2-13', '2-14', '1-13', '1-14', '1-15', '0-13', '0-14', '0-15', '0-16'],
            4: ['0-9', '0-10', '2-12', '1-10', '1-11', '3-12', '2-11', '1-12', '0-11', '0-12'],
            5: ['9-9', '9-10', '11-11', '10-10', '10-11', '10-12', '12-12', '11-12', '9-11', '9-12'],
        }
        
        puntas_activas_map = {
            2: [0, 3],
            3: [0, 4, 5],
            4: [1, 2, 4, 5],
            6: [0, 1, 2, 3, 4, 5],
        }
        
        puntas_activas = puntas_activas_map.get(partida.numero_jugadores, [0, 3])
        
        # Obtener todas las participaciones de la partida ordenadas
        participaciones = JugadorPartida.objects.filter(partida=partida).order_by('orden_participacion')
        
        piezas_actualizadas = 0
        
        for participacion in participaciones:
            punta_index = participacion.orden_participacion - 1
            punta_asignada = puntas_activas[punta_index]
            posiciones = posiciones_por_punta.get(punta_asignada, posiciones_por_punta[0])
            
            # Obtener las piezas del jugador en esta partida
            piezas = Pieza.objects.filter(jugador=participacion.jugador, partida=partida).order_by('id_pieza')
            
            # Actualizar cada pieza con su posición inicial
            for i, pieza in enumerate(piezas[:10]):
                if i < len(posiciones):
                    pieza.posicion = posiciones[i]
                    pieza.save()
                    piezas_actualizadas += 1
        
        return Response({
            'mensaje': 'Posiciones actualizadas correctamente',
            'piezas_actualizadas': piezas_actualizadas
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def registrar_movimientos(self, request, id_partida=None):
        """
        Registra una lista de movimientos para la partida indicada.
        Valida cada movimiento según las reglas del juego.
        """
        partida = self.get_object()
        movimientos_data = request.data.get('movimientos', [])
        if not isinstance(movimientos_data, list) or len(movimientos_data) == 0:
            return Response({ 'error': 'No hay movimientos para registrar' }, status=status.HTTP_400_BAD_REQUEST)

        occupied_positions = get_occupied_positions(partida.id_partida)

        created = []
        ultima_pieza = None
        ultimo_destino = None

        for idx, m in enumerate(movimientos_data, start=1):
            try:
                jugador_id = m.get('jugador_id')
                turno_id = m.get('turno_id')
                partida_id = m.get('partida_id')
                pieza_id = m.get('pieza_id')
                origen = m.get('origen')
                destino = m.get('destino')

                if not all([jugador_id, turno_id, pieza_id, origen, destino, partida_id]):
                    return Response({ 'error': f'Movimiento incompleto en índice {idx-1}' }, status=status.HTTP_400_BAD_REQUEST)

                if str(partida_id) != str(partida.id_partida):
                    return Response({ 'error': f'partida_id no coincide con la partida de la ruta: {partida_id} != {partida.id_partida}' }, status=status.HTTP_400_BAD_REQUEST)

                jugador = Jugador.objects.get(id_jugador=jugador_id)
                turno = Turno.objects.get(id_turno=turno_id)
                pieza = Pieza.objects.get(id_pieza=pieza_id)

                allow_simple = (idx == 1)
                es_valido, mensaje_error = validate_move(origen, destino, occupied_positions, allow_simple)
                if not es_valido:
                    return Response({ 
                        'error': f'Movimiento {idx} inválido: {mensaje_error}',
                        'origen': origen,
                        'destino': destino
                    }, status=status.HTTP_400_BAD_REQUEST)

                occupied_positions.discard(origen)
                occupied_positions.add(destino)

                mov = Movimiento.objects.create(
                    id_movimiento=f"M_{turno.id_turno}_{idx}_{datetime.now().timestamp()}",
                    jugador=jugador,
                    pieza=pieza,
                    turno=turno,
                    partida=partida,
                    origen=origen,
                    destino=destino,
                )
                created.append(mov)
                
                ultima_pieza = pieza
                ultimo_destino = destino
                
            except Jugador.DoesNotExist:
                return Response({ 'error': f'Jugador no encontrado: {jugador_id}' }, status=status.HTTP_400_BAD_REQUEST)
            except Turno.DoesNotExist:
                return Response({ 'error': f'Turno no encontrado: {turno_id}' }, status=status.HTTP_400_BAD_REQUEST)
            except Pieza.DoesNotExist:
                return Response({ 'error': f'Pieza no encontrada: {pieza_id}' }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({ 'error': str(e) }, status=status.HTTP_400_BAD_REQUEST)

        if ultima_pieza and ultimo_destino:
            ultima_pieza.posicion = ultimo_destino
            ultima_pieza.save()

        serializer = MovimientoSerializer(created, many=True)
        return Response({ 'registrados': serializer.data }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def avanzar_turno(self, request, id_partida=None):
        """
        Actualiza el turno actual con los datos proporcionados y crea el nuevo turno con los datos de entrada.
        """
        partida = self.get_object()
        old_turn_data = request.data.get('oldTurn')
        new_turn_data = request.data.get('newTurnCreated')

        if not new_turn_data:
            return Response({ 'error': 'newTurnCreated es requerido' }, status=status.HTTP_400_BAD_REQUEST)

        updated_turn = None
        if old_turn_data:
            turno_actual = partida.turnos.filter(fin__isnull=True).order_by('numero').first()
            if turno_actual:
                final_val = old_turn_data.get('final')
                inicio_val = old_turn_data.get('inicio')
                try:
                    if inicio_val:
                        if isinstance(inicio_val, (int, float)):
                            turno_actual.inicio = datetime.fromtimestamp(inicio_val / 1000.0, tz=timezone.get_current_timezone())
                        else:
                            turno_actual.inicio = datetime.fromisoformat(str(inicio_val))
                    if final_val:
                        if isinstance(final_val, (int, float)):
                            turno_actual.fin = datetime.fromtimestamp(final_val / 1000.0, tz=timezone.get_current_timezone())
                        else:
                            turno_actual.fin = datetime.fromisoformat(str(final_val))
                    else:
                        turno_actual.fin = timezone.now()
                except Exception:
                    turno_actual.fin = timezone.now()
                turno_actual.save()
                updated_turn = turno_actual

        numero_nuevo = new_turn_data.get('numero')
        inicio_nuevo = new_turn_data.get('inicio')
        jugador_id_nuevo = new_turn_data.get('jugador_id')

        if not all([numero_nuevo, jugador_id_nuevo]):
            return Response({ 'error': 'Faltan campos en newTurnCreated: numero y jugador_id son obligatorios' }, status=status.HTTP_400_BAD_REQUEST)

        try:
            jugador_nuevo = Jugador.objects.get(id_jugador=jugador_id_nuevo)
        except Jugador.DoesNotExist:
            return Response({ 'error': f'Jugador no encontrado: {jugador_id_nuevo}' }, status=status.HTTP_400_BAD_REQUEST)

        new_turn_id = f"T{numero_nuevo}_{partida.id_partida}"

        nuevo_turno = Turno(
            id_turno=new_turn_id,
            jugador=jugador_nuevo,
            numero=numero_nuevo,
            partida=partida
        )
        if inicio_nuevo:
            try:
                if isinstance(inicio_nuevo, (int, float)):
                    nuevo_turno.inicio = datetime.fromtimestamp(inicio_nuevo / 1000.0, tz=timezone.get_current_timezone())
                else:
                    nuevo_turno.inicio = datetime.fromisoformat(str(inicio_nuevo))
            except Exception:
                nuevo_turno.inicio = timezone.now()
        nuevo_turno.save()

        response_data = {
            'nuevo_turno': TurnoSerializer(nuevo_turno).data
        }
        if updated_turn:
            response_data['turno_actualizado'] = TurnoSerializer(updated_turn).data

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def end_game(self, request, id_partida=None):
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
            0: ['0-0', '0-1', '1-1', '0-2', '1-2', '2-2', '0-3', '1-3', '2-3', '3-3'],
            1: ['0-4', '0-5', '1-4', '1-5', '1-6', '2-4', '2-5', '3-4', '0-6', '0-7'],
            2: ['12-4', '9-6', '11-4', '11-5', '10-6', '10-4', '10-5', '9-5', '9-4', '9-7'],
            3: ['3-13', '2-13', '2-14', '1-13', '1-14', '1-15', '0-13', '0-14', '0-15', '0-16'],
            4: ['0-9', '0-10', '2-12', '1-10', '1-11', '3-12', '2-11', '1-12', '0-11', '0-12'],
            5: ['9-9', '9-10', '11-11', '10-10', '10-11', '10-12', '12-12', '11-12', '9-11', '9-12'],
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
                jugador=jugador,
                partida=partida
            )

    def destroy(self, request, *args, **kwargs):
        """
        Elimina la partida y todos los jugadores asociados creados para ella.
        También elimina en cascada: piezas, movimientos, turnos, IAs y chatbots.
        """
        partida = self.get_object()
        
        # Obtener todos los jugadores de esta partida
        jugadores_partida = JugadorPartida.objects.filter(partida=partida)
        jugadores_ids = [jp.jugador.id_jugador for jp in jugadores_partida]
        
        # Eliminar la partida (esto eliminará en cascada: turnos, movimientos, piezas, JugadorPartida)
        partida.delete()
        
        # Eliminar los jugadores que fueron creados para esta partida
        # (esto eliminará en cascada sus IAs y Chatbots asociados)
        Jugador.objects.filter(id_jugador__in=jugadores_ids).delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class PiezaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar piezas
    """
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        partida_id = self.request.query_params.get('partida_id')
        jugador_id = self.request.query_params.get('jugador_id')
        
        if partida_id:
            queryset = queryset.filter(partida_id=partida_id)
        if jugador_id:
            queryset = queryset.filter(jugador_id=jugador_id)
            
        return queryset

class TurnoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar turnos
    """
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        partida_id = self.request.query_params.get('partida_id')
        if partida_id:
            queryset = queryset.filter(partida_id=partida_id)
        return queryset


class MovimientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar movimientos
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
