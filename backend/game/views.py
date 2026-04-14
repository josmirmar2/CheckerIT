from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from datetime import datetime
from collections import deque
import re
from .ai.gemini_api import generate_gemini_reply, GeminiError, GeminiHttpError
from .models import Jugador, Partida, Pieza, Ronda, Movimiento, AgenteInteligente, Chatbot, JugadorPartida
from .ai.max_agent import MaxHeuristicAgent
from .ai.mcts_agent import MCTSAgent
from .serializers import (
    JugadorSerializer, PartidaSerializer, PartidaListSerializer,
    PiezaSerializer, RondaSerializer,
    MovimientoSerializer, AgenteInteligenteSerializer, ChatbotSerializer, JugadorPartidaSerializer
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


def _jump_neighbors(current_key, base_occupied_without_piece):
    """Devuelve destinos alcanzables con UN salto legal desde `current_key`.

    `base_occupied_without_piece` debe ser el conjunto de ocupadas EXCLUYENDO la posición
    original de la pieza (para poder simular el movimiento durante el encadenado).
    """
    current_coord = coord_from_key(current_key)
    if not current_coord:
        return []

    occupied = set(base_occupied_without_piece)
    occupied.add(current_key)

    neighbors = []
    for direction in AXIAL_DIRECTIONS:
        middle_q = current_coord["q"] + direction["dq"]
        middle_r = current_coord["r"] + direction["dr"]
        landing_q = current_coord["q"] + 2 * direction["dq"]
        landing_r = current_coord["r"] + 2 * direction["dr"]

        middle_key = key_from_coord(middle_q, middle_r)
        landing_key = key_from_coord(landing_q, landing_r)

        if not middle_key or not landing_key:
            continue
        if middle_key not in occupied:
            continue
        if landing_key in occupied:
            continue
        neighbors.append(landing_key)

    return neighbors


def find_jump_chain_path(origin_key, destination_key, occupied_positions):
    """Encuentra una ruta de saltos (encadenada) desde origen a destino.

    Retorna lista de claves [origen, ..., destino] si existe, si no None.
    La ruta está compuesta SOLO por saltos legales (no movimientos simples).
    """
    if not origin_key or not destination_key:
        return None
    if origin_key == destination_key:
        return None

    origin_coord = coord_from_key(origin_key)
    dest_coord = coord_from_key(destination_key)
    if not origin_coord or not dest_coord:
        return None
    if origin_key not in occupied_positions:
        return None
    if destination_key in occupied_positions:
        return None

    base_occupied_without_piece = set(occupied_positions)
    base_occupied_without_piece.discard(origin_key)

    queue = deque([origin_key])
    prev = {origin_key: None}

    while queue:
        current = queue.popleft()
        if current == destination_key:
            break
        for nxt in _jump_neighbors(current, base_occupied_without_piece):
            if nxt in prev:
                continue
            prev[nxt] = current
            queue.append(nxt)

    if destination_key not in prev:
        return None

    path = []
    cur = destination_key
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    if len(path) < 2:
        return None
    return path


def get_valid_moves_from(origin_key, occupied_positions, allow_simple=True):
    """Obtiene todos los movimientos válidos desde una posición."""
    simple = compute_simple_moves(origin_key, occupied_positions) if allow_simple else []
    jumps = compute_jump_moves(origin_key, occupied_positions)
    return list(set(simple + jumps))


def validate_move(origin_key, destination_key, occupied_positions, allow_simple=True):
    """
    Valida si un movimiento de origen a destino es válido.
    Retorna (es_válido: bool, mensaje_error: str)
    Reglas (GUIA_MOVIMIENTOS_PERMITIDOS):
    - Movimiento simple: a un nodo adyacente vacío (solo si allow_simple)
    - Salto: sobre una pieza (propia o rival) a un nodo vacío colineal detrás
    - No se permite avanzar más de un nodo sin salto
    """
    if not origin_key or not destination_key:
        return False, "Origen y destino son obligatorios"
    if origin_key == destination_key:
        return False, "Origen y destino no pueden ser iguales"

    origin_coord = coord_from_key(origin_key)
    dest_coord = coord_from_key(destination_key)
    if not origin_coord:
        return False, f"Origen fuera del tablero: {origin_key}"
    if not dest_coord:
        return False, f"Destino fuera del tablero: {destination_key}"

    if origin_key not in occupied_positions:
        return False, "No hay pieza en el origen"
    if destination_key in occupied_positions:
        return False, "El destino está ocupado"

    oq, or_ = origin_coord["q"], origin_coord["r"]
    dq, dr = dest_coord["q"], dest_coord["r"]

    for direction in AXIAL_DIRECTIONS:
        step_q = oq + direction["dq"]
        step_r = or_ + direction["dr"]
        step_key = key_from_coord(step_q, step_r)

        if allow_simple and step_key == destination_key:
            return True, ""

        landing_q = oq + 2 * direction["dq"]
        landing_r = or_ + 2 * direction["dr"]
        landing_key = key_from_coord(landing_q, landing_r)
        if landing_key != destination_key:
            continue
        if not step_key:
            continue
        if step_key not in occupied_positions:
            continue
        return True, ""

    if allow_simple:
        return False, "Movimiento inválido: no es adyacente ni salto legal"
    return False, "Movimiento inválido: en cadena solo se permiten saltos legales"




class JugadorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar jugadores
    """
    queryset = Jugador.objects.all()
    serializer_class = JugadorSerializer

    def _ensure_ai_name(self, jugador, request_data):
        if jugador.humano:
            return
        dificultad = str(request_data.get('dificultad') or request_data.get('nivel') or 'Fácil')
        numero = jugador.numero or Jugador.objects.filter(humano=False).count()
        nombre_deseado = f"Agente Inteligente {numero}"
        if jugador.nombre != nombre_deseado:
            jugador.nombre = nombre_deseado
            jugador.save(update_fields=['nombre'])

    def perform_create(self, serializer):
        jugador = serializer.save()
        self._ensure_ai_name(jugador, self.request.data)

    def perform_update(self, serializer):
        jugador = serializer.save()
        self._ensure_ai_name(jugador, self.request.data)


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
                {"nombre": "Agente Inteligente Difícil 2", "icono": "Robot-icon.jpg", "tipo": "agente_inteligente", "dificultad": "Difícil"}
            ]
        }
        """
        jugadores_data = request.data.get('jugadores', [])
        numero_jugadores_raw = request.data.get('numero_jugadores', None)
        
        if not jugadores_data or len(jugadores_data) == 0:
            return Response(
                {'error': 'Se requieren datos de jugadores'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determinar/validar numero_jugadores
        if numero_jugadores_raw is None:
            numero_jugadores = len(jugadores_data)
        else:
            try:
                numero_jugadores = int(numero_jugadores_raw)
            except Exception:
                return Response({'error': 'numero_jugadores debe ser un entero'}, status=status.HTTP_400_BAD_REQUEST)

        if numero_jugadores < 2 or numero_jugadores > 6:
            return Response({'error': 'Una partida debe tener entre 2 y 6 jugadores'}, status=status.HTTP_400_BAD_REQUEST)

        if len(jugadores_data) != numero_jugadores:
            return Response(
                {'error': 'numero_jugadores no coincide con la cantidad de jugadores enviada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar que no se repitan numeros de jugador dentro de la partida (p.ej. dos numero=1)
        numeros = []
        for idx, jugador_data in enumerate(jugadores_data):
            numero_raw = jugador_data.get('numero', idx + 1)
            try:
                numero = int(numero_raw)
            except Exception:
                return Response({'error': f'El campo numero del jugador {idx + 1} debe ser un entero'}, status=status.HTTP_400_BAD_REQUEST)
            numeros.append(numero)

        if len(set(numeros)) != len(numeros):
            return Response({'error': 'No puede haber dos jugadores con el mismo numero en la misma partida'}, status=status.HTTP_400_BAD_REQUEST)
        
        jugadores_list = []
        
        for idx, jugador_data in enumerate(jugadores_data):
            es_humano = jugador_data.get('tipo', 'humano') == 'humano'
            numero = numeros[idx]
            dificultad = jugador_data.get('dificultad', 'Fácil')

            if es_humano:
                nombre = jugador_data.get('nombre', f'Jugador {idx + 1}')
            else:
                nombre = f"Agente Inteligente {numero}"
            
            jugador = Jugador.objects.create(
                id_jugador=f"J{idx + 1}_{datetime.now().timestamp()}",
                nombre=nombre,
                humano=es_humano,
                numero=numero
            )
            
            if not es_humano:
                nivel = 2 if dificultad == 'Difícil' else 1
                
                AgenteInteligente.objects.create(
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
        
        Ronda.objects.create(
            id_ronda=f"R1_{partida.id_partida}",
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

        ronda_actual = partida.rondas.filter(fin__isnull=True).order_by('numero').first()
        if not ronda_actual:
            return Response({ 'error': 'No hay ronda activa para la partida' }, status=status.HTTP_400_BAD_REQUEST)

        created = []
        piece_positions = {}
        moved_piece_id = None
        expected_jugador_id = None
        expected_ronda_id = None
        expected_partida_id = str(partida.id_partida)
        chain_mode = len(movimientos_data) > 1

        for idx, m in enumerate(movimientos_data, start=1):
            try:
                jugador_id = m.get('jugador_id')
                ronda_id = m.get('ronda_id')
                partida_id = m.get('partida_id')
                pieza_id = m.get('pieza_id')
                origen = m.get('origen')
                destino = m.get('destino')

                if not all([jugador_id, ronda_id, pieza_id, origen, destino, partida_id]):
                    return Response({ 'error': f'Movimiento incompleto en índice {idx-1}' }, status=status.HTTP_400_BAD_REQUEST)

                if str(partida_id) != expected_partida_id:
                    return Response({ 'error': f'partida_id no coincide con la partida de la ruta: {partida_id} != {partida.id_partida}' }, status=status.HTTP_400_BAD_REQUEST)

                if expected_jugador_id is None:
                    expected_jugador_id = str(jugador_id)
                elif str(jugador_id) != expected_jugador_id:
                    return Response({ 'error': 'Todos los movimientos deben pertenecer al mismo jugador' }, status=status.HTTP_400_BAD_REQUEST)

                if expected_ronda_id is None:
                    expected_ronda_id = str(ronda_id)
                elif str(ronda_id) != expected_ronda_id:
                    return Response({ 'error': 'Todos los movimientos deben pertenecer a la misma ronda' }, status=status.HTTP_400_BAD_REQUEST)

                if moved_piece_id is None:
                    moved_piece_id = str(pieza_id)
                elif str(pieza_id) != moved_piece_id:
                    return Response({ 'error': 'No se permite mover varias piezas en una misma ronda' }, status=status.HTTP_400_BAD_REQUEST)

                jugador = Jugador.objects.get(id_jugador=jugador_id)
                ronda = Ronda.objects.get(id_ronda=ronda_id)
                pieza = Pieza.objects.get(id_pieza=pieza_id)

                enforce_move_rules = (not bool(getattr(jugador, 'humano', False))) or bool(getattr(settings, 'ENFORCE_MOVE_VALIDATION_FOR_HUMANS', False))

                # Validaciones de ronda/jugador/pieza
                if str(ronda.partida_id) != expected_partida_id:
                    return Response({ 'error': 'La ronda no pertenece a la partida' }, status=status.HTTP_400_BAD_REQUEST)
                if ronda.fin is not None:
                    return Response({ 'error': 'La ronda ya está finalizada' }, status=status.HTTP_400_BAD_REQUEST)
                if str(ronda_actual.id_ronda) != str(ronda.id_ronda):
                    return Response({ 'error': 'No es la ronda activa de la partida' }, status=status.HTTP_400_BAD_REQUEST)
                if str(ronda.jugador_id) != str(jugador.id_jugador):
                    return Response({ 'error': 'El jugador del movimiento no coincide con el jugador de la ronda' }, status=status.HTTP_400_BAD_REQUEST)
                if str(pieza.partida_id) != expected_partida_id:
                    return Response({ 'error': 'La pieza no pertenece a la partida' }, status=status.HTTP_400_BAD_REQUEST)
                if str(pieza.jugador_id) != str(jugador.id_jugador):
                    return Response({ 'error': 'La pieza no pertenece al jugador' }, status=status.HTTP_400_BAD_REQUEST)

                expected_origin = pieza.posicion
                if pieza_id in piece_positions:
                    expected_origin = piece_positions[pieza_id][1]
                if str(origen) != str(expected_origin):
                    return Response({
                        'error': 'El origen no coincide con la posición actual de la pieza',
                        'origen_recibido': origen,
                        'origen_esperado': expected_origin,
                    }, status=status.HTTP_400_BAD_REQUEST)

                if enforce_move_rules:
                    allow_simple = (not chain_mode and idx == 1)
                    es_valido, mensaje_error = validate_move(origen, destino, occupied_positions, allow_simple)
                    if not es_valido:
                        if bool(getattr(jugador, 'humano', False)) and (not chain_mode) and idx == 1:
                            path = find_jump_chain_path(origen, destino, occupied_positions)
                            if path and len(path) >= 2:
                                for step_i in range(len(path) - 1):
                                    step_origen = path[step_i]
                                    step_destino = path[step_i + 1]

                                    step_ok, step_err = validate_move(step_origen, step_destino, occupied_positions, allow_simple=False)
                                    if not step_ok:
                                        return Response({
                                            'error': f'Movimiento {idx} inválido: {step_err}',
                                            'origen': step_origen,
                                            'destino': step_destino,
                                        }, status=status.HTTP_400_BAD_REQUEST)

                                    occupied_positions.discard(step_origen)
                                    occupied_positions.add(step_destino)

                                    mov = Movimiento.objects.create(
                                        id_movimiento=f"M_{ronda.id_ronda}_{idx}_{step_i + 1}_{datetime.now().timestamp()}",
                                        jugador=jugador,
                                        pieza=pieza,
                                        ronda=ronda,
                                        partida=partida,
                                        origen=step_origen,
                                        destino=step_destino,
                                    )
                                    created.append(mov)

                                piece_positions[pieza_id] = (pieza, destino)
                                continue

                        return Response({
                            'error': f'Movimiento {idx} inválido: {mensaje_error}',
                            'origen': origen,
                            'destino': destino
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Humanos: validación mínima de consistencia (las reglas se validan en frontend)
                    if not coord_from_key(origen):
                        return Response({ 'error': f'Origen fuera del tablero: {origen}', 'origen': origen }, status=status.HTTP_400_BAD_REQUEST)
                    if not coord_from_key(destino):
                        return Response({ 'error': f'Destino fuera del tablero: {destino}', 'destino': destino }, status=status.HTTP_400_BAD_REQUEST)
                    if origen not in occupied_positions:
                        return Response({ 'error': 'No hay pieza en el origen', 'origen': origen }, status=status.HTTP_400_BAD_REQUEST)
                    if destino in occupied_positions:
                        return Response({ 'error': 'El destino está ocupado', 'destino': destino }, status=status.HTTP_400_BAD_REQUEST)

                    # Si el humano envía un destino final de una cadena de saltos, intentamos expandirla.
                    if (not chain_mode) and idx == 1:
                        path = find_jump_chain_path(origen, destino, occupied_positions)
                        if path and len(path) >= 2:
                            for step_i in range(len(path) - 1):
                                step_origen = path[step_i]
                                step_destino = path[step_i + 1]

                                # Validación mínima por paso: origen ocupado y destino libre.
                                if step_origen not in occupied_positions:
                                    return Response({ 'error': 'No hay pieza en el origen', 'origen': step_origen }, status=status.HTTP_400_BAD_REQUEST)
                                if step_destino in occupied_positions:
                                    return Response({ 'error': 'El destino está ocupado', 'destino': step_destino }, status=status.HTTP_400_BAD_REQUEST)

                                occupied_positions.discard(step_origen)
                                occupied_positions.add(step_destino)

                                mov = Movimiento.objects.create(
                                    id_movimiento=f"M_{ronda.id_ronda}_{idx}_{step_i + 1}_{datetime.now().timestamp()}",
                                    jugador=jugador,
                                    pieza=pieza,
                                    ronda=ronda,
                                    partida=partida,
                                    origen=step_origen,
                                    destino=step_destino,
                                )
                                created.append(mov)

                            piece_positions[pieza_id] = (pieza, destino)
                            continue

                occupied_positions.discard(origen)
                occupied_positions.add(destino)

                mov = Movimiento.objects.create(
                    id_movimiento=f"M_{ronda.id_ronda}_{idx}_{datetime.now().timestamp()}",
                    jugador=jugador,
                    pieza=pieza,
                    ronda=ronda,
                    partida=partida,
                    origen=origen,
                    destino=destino,
                )
                created.append(mov)

                # Guardar el último destino de esta pieza (en caso de movimientos encadenados)
                piece_positions[pieza_id] = (pieza, destino)
                
            except Jugador.DoesNotExist:
                return Response({ 'error': f'Jugador no encontrado: {jugador_id}' }, status=status.HTTP_400_BAD_REQUEST)
            except Ronda.DoesNotExist:
                return Response({ 'error': f'Ronda no encontrada: {ronda_id}' }, status=status.HTTP_400_BAD_REQUEST)
            except Pieza.DoesNotExist:
                return Response({ 'error': f'Pieza no encontrada: {pieza_id}' }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({ 'error': str(e) }, status=status.HTTP_400_BAD_REQUEST)

        # Guardar posiciones finales de TODAS las piezas movidas
        for pieza, destino in piece_positions.values():
            pieza.posicion = destino
            pieza.save()

        serializer = MovimientoSerializer(created, many=True)
        return Response({ 'registrados': serializer.data }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def avanzar_ronda(self, request, id_partida=None):
        """Actualiza la ronda actual y crea la nueva ronda."""
        partida = self.get_object()
        old_round_data = request.data.get('oldRound')
        new_round_data = request.data.get('newRoundCreated')

        if not new_round_data:
            return Response({ 'error': 'newRoundCreated es requerido' }, status=status.HTTP_400_BAD_REQUEST)

        updated_round = None
        if old_round_data:
            ronda_actual = partida.rondas.filter(fin__isnull=True).order_by('numero').first()
            if ronda_actual:
                final_val = old_round_data.get('final')
                inicio_val = old_round_data.get('inicio')
                try:
                    if inicio_val:
                        if isinstance(inicio_val, (int, float)):
                            ronda_actual.inicio = datetime.fromtimestamp(inicio_val / 1000.0, tz=timezone.get_current_timezone())
                        else:
                            ronda_actual.inicio = datetime.fromisoformat(str(inicio_val))
                    if final_val:
                        if isinstance(final_val, (int, float)):
                            ronda_actual.fin = datetime.fromtimestamp(final_val / 1000.0, tz=timezone.get_current_timezone())
                        else:
                            ronda_actual.fin = datetime.fromisoformat(str(final_val))
                    else:
                        ronda_actual.fin = timezone.now()
                except Exception:
                    ronda_actual.fin = timezone.now()
                ronda_actual.save()
                updated_round = ronda_actual

        numero_nuevo = new_round_data.get('numero')
        inicio_nuevo = new_round_data.get('inicio')
        jugador_id_nuevo = new_round_data.get('jugador_id')

        if not all([numero_nuevo, jugador_id_nuevo]):
            return Response({ 'error': 'Faltan campos en newRoundCreated: numero y jugador_id son obligatorios' }, status=status.HTTP_400_BAD_REQUEST)

        try:
            jugador_nuevo = Jugador.objects.get(id_jugador=jugador_id_nuevo)
        except Jugador.DoesNotExist:
            return Response({ 'error': f'Jugador no encontrado: {jugador_id_nuevo}' }, status=status.HTTP_400_BAD_REQUEST)

        new_round_id = f"R{numero_nuevo}_{partida.id_partida}"

        nueva_ronda = Ronda(
            id_ronda=new_round_id,
            jugador=jugador_nuevo,
            numero=numero_nuevo,
            partida=partida
        )
        if inicio_nuevo:
            try:
                if isinstance(inicio_nuevo, (int, float)):
                    nueva_ronda.inicio = datetime.fromtimestamp(inicio_nuevo / 1000.0, tz=timezone.get_current_timezone())
                else:
                    nueva_ronda.inicio = datetime.fromisoformat(str(inicio_nuevo))
            except Exception:
                nueva_ronda.inicio = timezone.now()
        nueva_ronda.save()

        response_data = {
            'nueva_ronda': RondaSerializer(nueva_ronda).data
        }
        if updated_round:
            response_data['ronda_actualizada'] = RondaSerializer(updated_round).data

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
        
        ronda_actual = partida.rondas.filter(fin__isnull=True).first()
        if ronda_actual:
            ronda_actual.fin = timezone.now()
            ronda_actual.save()
        
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
        También elimina en cascada: piezas, movimientos, rondas, agentes Inteligentes y chatbots.
        """
        partida = self.get_object()
        
        # Obtener todos los jugadores de esta partida
        jugadores_partida = JugadorPartida.objects.filter(partida=partida)
        jugadores_ids = [jp.jugador.id_jugador for jp in jugadores_partida]
        
        # Eliminar la partida (esto eliminará en cascada: rondas, movimientos, piezas, JugadorPartida)
        partida.delete()
        
        # Eliminar los jugadores que fueron creados para esta partida
        # (esto eliminará en cascada sus agentes Inteligentes y Chatbots asociados)
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

class RondaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar rondas
    """
    queryset = Ronda.objects.all()
    serializer_class = RondaSerializer
    
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
        ronda_id = self.request.query_params.get('ronda_id')
        if ronda_id:
            queryset = queryset.filter(ronda_id=ronda_id)
        return queryset


class AgenteInteligenteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar configuraciones de agente Inteligente
    """
    queryset = AgenteInteligente.objects.all()
    serializer_class = AgenteInteligenteSerializer
    lookup_field = 'pk'
    lookup_value_regex = '[^/]+'

    @action(detail=True, methods=['post'])
    def sugerir_movimiento(self, request, pk=None):
        """
        Retorna un movimiento sugerido para el agente Inteligente usando heurística Max.

        Datos de entrada:
        - partida_id: id de la partida
        - permitir_simples (opcional, bool): si True incluye movimientos simples en el primer salto
        """
        agente_obj = self.get_object() 
        partida_id = request.data.get('partida_id')
        permitir_simples_raw = request.data.get('permitir_simples', True)

        if not partida_id:
            return Response({'error': 'partida_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        ronda_actual = Ronda.objects.filter(partida_id=partida_id, fin__isnull=True).order_by('numero').first()
        if not ronda_actual:
            return Response({'error': 'No hay ronda activa para la partida'}, status=status.HTTP_400_BAD_REQUEST)
        if str(ronda_actual.jugador_id) != str(agente_obj.jugador_id):
            return Response({'error': 'No es la ronda de este agente Inteligente'}, status=status.HTTP_409_CONFLICT)

        allow_simple = bool(permitir_simples_raw) if isinstance(permitir_simples_raw, bool) else str(permitir_simples_raw).lower() != 'false'

        try:
            # Nivel 1: heurística Max (actual). Nivel 2: MCTS (DIFICIL).
            if int(getattr(agente_obj, 'nivel', 1) or 1) >= 2:
                iterations_raw = request.data.get('simulaciones', request.data.get('iterations', 250))
                depth_raw = request.data.get('rollout_depth', 10)
                try:
                    iterations = int(iterations_raw)
                except Exception:
                    iterations = 250
                try:
                    rollout_depth = int(depth_raw)
                except Exception:
                    rollout_depth = 10

                agent = MCTSAgent()
                sugerencia = agent.suggest_move(
                    partida_id=partida_id,
                    jugador_id=agente_obj.jugador_id,
                    allow_simple=allow_simple,
                    iterations=max(1, min(iterations, 2000)),
                    rollout_depth=max(1, min(rollout_depth, 60)),
                )
            else:
                agent = MaxHeuristicAgent()
                sugerencia = agent.suggest_move(
                    partida_id=partida_id,
                    jugador_id=agente_obj.jugador_id,
                    allow_simple=allow_simple,
                )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc: 
            return Response({'error': f'No se pudo calcular la jugada: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(sugerencia, status=status.HTTP_200_OK)


class ChatbotViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el chatbot
    """
    queryset = Chatbot.objects.all()
    serializer_class = ChatbotSerializer

    def _build_gemini_history(self, chatbot: Chatbot, *, limit_turns: int = 10) -> list[dict]:
        conversaciones = (chatbot.memoria or {}).get('conversaciones') or []
        history: list[dict] = []
        for turn in conversaciones[-limit_turns:]:
            mensaje = (turn or {}).get('mensaje')
            respuesta = (turn or {}).get('respuesta')
            if mensaje:
                history.append({"role": "user", "parts": [{"text": str(mensaje)}]})
            if respuesta:
                history.append({"role": "model", "parts": [{"text": str(respuesta)}]})
        return history

    def _sanitize_llm_text(self, text: str | None) -> str:
        if text is None:
            return ""
        s = str(text)

        # Quitar marcas típicas de negrita Markdown conservando el contenido.
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s, flags=re.DOTALL)
        s = re.sub(r"__(.+?)__", r"\1", s, flags=re.DOTALL)

        # Si quedaron marcadores sueltos, eliminarlos.
        s = s.replace("**", "").replace("__", "")
        return s

    def _get_domain_keywords(self) -> list[str]:
        raw = getattr(settings, 'CHATBOT_DOMAIN_KEYWORDS', '')
        keywords: list[str] = []
        if raw and str(raw).strip():
            keywords = [k.strip().lower() for k in str(raw).split(',') if k.strip()]
        if not keywords:
            keywords = [
                'checkerit',
                'damas',
                'damas chinas',
                'reglas',
                'movimiento',
                'mover',
                'salto',
                'saltos',
                'cadena',
                'ronda',
                'turno',
                'partida',
                'tablero',
                'pieza',
                'piezas',
                'jugador',
                'interfaz',
                'ui',
                'boton',
                'botón',
                'pausa',
                'musica',
                'música',
                'ayuda',
                'asistente',
                'cómo jugar',
                'como jugar',
                'hola',
                'buenas',
            ]
        return keywords

    def _is_in_domain(self, mensaje: str) -> bool:
        if mensaje is None:
            return False
        texto = str(mensaje).lower()
        for kw in self._get_domain_keywords():
            if kw and kw in texto:
                return True
        return False

    def _maybe_answer_game_help(
        self,
        *,
        chatbot: Chatbot,
        mensaje: str,
        partida_id: str | None,
        jugador_id: str | None,
        pieza_id: str | None = None,
    ) -> tuple[str | None, dict | None]:
        """Respuestas deterministas basadas en estado de partida.

        Devuelve (respuesta_texto, extra_payload) o (None, None) si no aplica.
        """
        texto = (str(mensaje) if mensaje is not None else "").lower()

        best_move_triggers = (
            "mejor jugada",
            "mejor movimiento",
            "sugerir jugada",
            "sugerencia",
            "recomienda",
            "qué jugada",
            "que jugada",
            "best move",
        )
        possible_moves_triggers = (
            "movimientos posibles",
            "posibles movimientos",
            "posiciones posibles",
            "donde puedo mover",
            "dónde puedo mover",
            "a donde puedo mover",
            "a dónde puedo mover",
            "ver movimientos",
        )
        how_to_move_triggers = (
            "como se mueve",
            "cómo se mueve",
            "como mover",
            "cómo mover",
            "como puedo mover",
            "cómo puedo mover",
        )

        end_game_triggers = (
            "terminar partida",
            "acabar partida",
            "finalizar partida",
            "cancelar partida",
            "cómo terminar",
            "como terminar",
            "cómo acabar",
            "como acabar",
            "finalizar",
            "cancelar",
            "ganador",
            "victoria",
            "cómo ganar",
            "como ganar",
        )

        show_move_triggers = (
            "muestramelo",
            "muéstramelo",
            "muestrame",
            "muéstrame",
            "muestra el movimiento",
            "mostrar movimiento",
            "muéstrame el movimiento",
            "muestrame el movimiento",
            "en pantalla",
        )

        confirm_triggers = (
            "si",
            "sí",
            "vale",
            "ok",
            "de acuerdo",
            "perfecto",
        )

        wants_best = any(t in texto for t in best_move_triggers)
        wants_possible = any(t in texto for t in possible_moves_triggers)
        wants_how = any(t in texto for t in how_to_move_triggers)
        wants_end = any(t in texto for t in end_game_triggers)
        wants_show = any(t in texto for t in show_move_triggers)

        last_best_move = (chatbot.memoria or {}).get("last_best_move")
        awaiting_show_move = bool((chatbot.memoria or {}).get("awaiting_show_move"))
        texto_stripped = texto.strip()
        confirms_show = awaiting_show_move and any(
            texto_stripped == t or texto_stripped.startswith(f"{t} ")
            for t in confirm_triggers
        )

        if (wants_show or confirms_show) and not wants_best:
            if not isinstance(last_best_move, dict) or not last_best_move:
                return (
                    "Primero pídeme 'cuál es la mejor jugada' y después dime 'muéstramelo' para resaltarla en el tablero.",
                    {"tipo": "mostrar_movimiento_no_disponible"},
                )
            origen = last_best_move.get("origen")
            destino = last_best_move.get("destino")
            return (
                f"De acuerdo. Te muestro en pantalla el movimiento sugerido: {origen} -> {destino}.",
                {"tipo": "mostrar_movimiento", "sugerencia": last_best_move},
            )

        if wants_end and not wants_best:
            respuesta = (
                "Puedes terminar una partida de dos formas:\n\n"
                "1) Cancelarla / finalizarla manualmente (antes de que haya ganador):\n"
                "   - Pausa el juego y pulsa el botón de Finalizar.\n"
                "   - Confirma la acción: volverás al inicio y se pierde el progreso de la partida.\n\n"
                "2) Terminarla de forma normal (con ganador):\n"
                "   - Sigue jugando turnos hasta que un jugador complete su objetivo.\n"
                "   - La partida termina cuando todas las piezas de un jugador llegan a la zona objetivo (la punta opuesta).\n"
                "   - En ese momento se muestra la pantalla de victoria con el ganador."
            )
            return respuesta, {"tipo": "fin_partida"}

        if wants_how and not wants_best:
            respuesta = (
                "En CheckerIT puedes mover una pieza de dos formas:\n"
                "1) Movimiento simple: a una casilla vecina vacía.\n"
                "2) Salto: si hay una pieza adyacente (propia o rival), puedes saltarla y caer en la casilla colineal detrás si está vacía.\n\n"
                "Los saltos se pueden encadenar si, tras aterrizar, existe otro salto legal.\n\n"
                "Botones durante tu turno:\n"
                "- Pasar Ronda: cede el turno sin mover (si aún no has hecho un movimiento).\n"
                "- Deshacer: revierte el movimiento que acabas de realizar en la ronda actual.\n"
                "- Continuar: confirma el movimiento hecho y pasa al siguiente turno."
            )
            return respuesta, {"tipo": "reglas_movimiento"}

        # Desactivado: no se ofrece la funcionalidad de "movimientos posibles" desde el chatbot.
        if wants_possible and not wants_best:
            return (
                "Ahora mismo el asistente no ofrece la opción de listar 'movimientos/posiciones posibles'. "
                "Si quieres, puedes preguntar por 'la mejor jugada' o por 'cómo se mueve una pieza'.",
                {"tipo": "movimientos_no_disponible"},
            )

        if not wants_best:
            return None, None

        if not partida_id or not jugador_id:
            return (
                "Para poder ayudarte con jugadas/movimientos necesito el estado de la partida (partida_id) y el jugador actual (jugador_id).",
                {"tipo": "faltan_parametros"},
            )

        # Validar existencia de partida/jugador y    evitar respuestas confusas
        if not Partida.objects.filter(id_partida=str(partida_id)).exists():
            return (f"partida_id no válido: {partida_id}", {"tipo": "error", "campo": "partida_id"})
        if not Jugador.objects.filter(id_jugador=str(jugador_id)).exists():
            return (f"jugador_id no válido: {jugador_id}", {"tipo": "error", "campo": "jugador_id"})

        if wants_best:
            try:
                agent = MCTSAgent()
                sugerencia = agent.suggest_move(
                    partida_id=str(partida_id),
                    jugador_id=str(jugador_id),
                    allow_simple=True,
                    iterations=250,
                )
            except ValueError as exc:
                return (f"No pude calcular la mejor jugada: {exc}", {"tipo": "error", "motivo": "sin_jugadas"})
            except Exception as exc:
                return (f"No se pudo calcular la jugada: {exc}", {"tipo": "error"})

            origen = sugerencia.get("origen")
            destino = sugerencia.get("destino")
            secuencia = sugerencia.get("secuencia")
            if isinstance(secuencia, list) and secuencia:
                pasos = " -> ".join([str(origen)] + [str(step.get("destino")) for step in secuencia if step.get("destino")])
                respuesta = f"El mejor movimiento que se puede realizar según el análisis realizado por la aplicación es: {pasos}.\n\n¿Quieres que te muestre en pantalla el movimiento?"
            else:
                respuesta = f"El mejor movimiento que se puede realizar según el análisis realizado por la aplicación es: {origen} -> {destino}.\n\n¿Quieres que te muestre en pantalla el movimiento?"

            return respuesta, {"tipo": "mejor_jugada", "sugerencia": sugerencia}

        # Nota: el caso de movimientos posibles se gestiona arriba como "no disponible".

    def _send_and_persist(
        self,
        *,
        chatbot: Chatbot,
        mensaje: str,
        partida_id: str | None = None,
        jugador_id: str | None = None,
        pieza_id: str | None = None,
    ) -> Response:
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        try:
            max_chars = int(getattr(settings, 'CHATBOT_MAX_INPUT_CHARS', 400))
        except Exception:
            max_chars = 400
        if max_chars < 1:
            max_chars = 400
        if mensaje is None:
            mensaje = ''
        mensaje = str(mensaje)

        if len(mensaje.strip()) == 0:
            return Response({'error': 'El mensaje no puede estar vacío'}, status=status.HTTP_400_BAD_REQUEST)
        if len(mensaje) > max_chars:
            return Response(
                {'error': f'El mensaje es demasiado largo (máx {max_chars} caracteres)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Si el mensaje pide ayuda de jugadas/movimientos y se aporta contexto, responder sin Gemini.
        respuesta_local, extra = self._maybe_answer_game_help(
            chatbot=chatbot,
            mensaje=mensaje,
            partida_id=partida_id,
            jugador_id=jugador_id,
            pieza_id=pieza_id,
        )
        if respuesta_local is not None:
            respuesta_local = self._sanitize_llm_text(respuesta_local)
            if 'conversaciones' not in chatbot.memoria:
                chatbot.memoria['conversaciones'] = []

            # Persistir estado útil para "muéstramelo"
            if isinstance(extra, dict):
                if extra.get("tipo") == "mejor_jugada" and isinstance(extra.get("sugerencia"), dict):
                    chatbot.memoria["last_best_move"] = extra.get("sugerencia")
                    chatbot.memoria["awaiting_show_move"] = True
                elif extra.get("tipo") in {"mostrar_movimiento", "mostrar_movimiento_no_disponible"}:
                    chatbot.memoria["awaiting_show_move"] = False

            chatbot.memoria['conversaciones'].append({
                'mensaje': mensaje,
                'respuesta': respuesta_local,
                'timestamp': str(timezone.now())
            })
            chatbot.save()

            payload = {'chatbot_id': chatbot.id, 'respuesta': respuesta_local}
            if isinstance(extra, dict) and extra:
                payload.update(extra)
            return Response(payload, status=status.HTTP_200_OK)

        # Hard gate: si se fuerza dominio y el mensaje no es del dominio, rechazar sin IA
        if getattr(settings, 'CHATBOT_DOMAIN_ENFORCE', True) and not self._is_in_domain(mensaje):
            respuesta = getattr(
                settings,
                'CHATBOT_REFUSAL_MESSAGE',
                'Solo puedo ayudarte con CheckerIT (reglas del juego e interfaz).',
            )
            if 'conversaciones' not in chatbot.memoria:
                chatbot.memoria['conversaciones'] = []
            chatbot.memoria['conversaciones'].append({
                'mensaje': mensaje,
                'respuesta': respuesta,
                'timestamp': str(timezone.now())
            })
            chatbot.save()
            return Response({'chatbot_id': chatbot.id, 'respuesta': respuesta}, status=status.HTTP_200_OK)

        if not api_key:
            # Fallback para entornos sin configuración de Gemini (tests, dev)
            respuesta = f"Respuesta del chatbot a: {mensaje}"
        else:
            try:
                respuesta = generate_gemini_reply(
                    api_key=api_key,
                    model=getattr(settings, 'GEMINI_MODEL', None),
                    timeout_seconds=int(getattr(settings, 'GEMINI_TIMEOUT_SECONDS', 15)),
                    api_version=getattr(settings, 'GEMINI_API_VERSION', 'v1'),
                    max_retries=int(getattr(settings, 'GEMINI_MAX_RETRIES', 2)),
                    retry_backoff_seconds=float(getattr(settings, 'GEMINI_RETRY_BACKOFF_SECONDS', 0.6)),
                    system_prompt=getattr(settings, 'GEMINI_SYSTEM_PROMPT', None),
                    temperature=float(getattr(settings, 'GEMINI_TEMPERATURE', 0.2)),
                    max_output_tokens=int(getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 256)),
                    user_message=mensaje,
                    history=self._build_gemini_history(chatbot, limit_turns=10),
                )
            except GeminiHttpError as exc:
                return Response({'error': str(exc)}, status=exc.status_code)
            except GeminiError as exc:
                return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        respuesta = self._sanitize_llm_text(respuesta)

        if 'conversaciones' not in chatbot.memoria:
            chatbot.memoria['conversaciones'] = []

        chatbot.memoria['conversaciones'].append({
            'mensaje': mensaje,
            'respuesta': respuesta,
            'timestamp': str(timezone.now())
        })
        chatbot.save()

        return Response({'chatbot_id': chatbot.id, 'respuesta': respuesta}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='send_message')
    def send_message_global(self, request):
        """Envía un mensaje a Gemini y guarda la conversación.

        Body JSON:
        - mensaje: str (obligatorio)
        - chatbot_id: int (opcional; si no, usa el primero o crea uno)
        """
        mensaje = request.data.get('mensaje', '')
        chatbot_id = request.data.get('chatbot_id')
        partida_id = request.data.get('partida_id')
        jugador_id = request.data.get('jugador_id')
        pieza_id = request.data.get('pieza_id')

        if chatbot_id:
            try:
                chatbot = Chatbot.objects.get(id=chatbot_id)
            except Chatbot.DoesNotExist:
                return Response({'error': 'chatbot_id no válido'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            chatbot = Chatbot.objects.order_by('id').first()
            if chatbot is None:
                chatbot = Chatbot.objects.create()

        return self._send_and_persist(
            chatbot=chatbot,
            mensaje=mensaje,
            partida_id=partida_id,
            jugador_id=jugador_id,
            pieza_id=pieza_id,
        )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Envía un mensaje al chatbot y obtiene respuesta
        """
        chatbot = self.get_object()
        mensaje = request.data.get('mensaje', '')
        partida_id = request.data.get('partida_id')
        jugador_id = request.data.get('jugador_id')
        pieza_id = request.data.get('pieza_id')

        return self._send_and_persist(
            chatbot=chatbot,
            mensaje=mensaje,
            partida_id=partida_id,
            jugador_id=jugador_id,
            pieza_id=pieza_id,
        )


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
