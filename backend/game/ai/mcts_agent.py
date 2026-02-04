from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import random
from typing import Dict, Iterable, List, Optional, Set, Tuple

from montecarlo.node import Node
from montecarlo.montecarlo import MonteCarlo

from ..models import JugadorPartida, Pieza, Turno
from .max_agent import (
    AXIAL_DIRECTIONS,
    GOAL_POSITIONS,
    _axial_from_key,
    _key_from_axial,
    _parse_punta,
    _target_punta,
)


@dataclass
class Move:
    pieza_id: str
    origen: str
    destino: str
    sequence: Optional[List[str]] = None


class ChineseCheckersState:
    def __init__(
        self,
        positions: Dict[str, str],
        piece_owner: Dict[str, str],
        piece_type: Dict[str, str],
        players_order: List[str],
        current_index: int,
        target_by_player: Dict[str, int],
        allow_simple: bool = True,
        last_move: Optional[Move] = None,
    ) -> None:
        self.positions = positions
        self.piece_owner = piece_owner
        self.piece_type = piece_type
        self.players_order = players_order
        self.current_index = current_index
        self.target_by_player = target_by_player
        self.allow_simple = allow_simple
        self.last_move = last_move

    def current_player_id(self) -> str:
        return self.players_order[self.current_index]

    def get_possible_moves(self) -> List[Move]:
        occupied = {pos for pos in self.positions.values() if pos}
        current_player = self.current_player_id()
        moves: List[Move] = []

        for pieza_id, owner_id in self.piece_owner.items():
            if owner_id != current_player:
                continue
            
            origin = self.positions.get(pieza_id)
            if not origin:
                continue

            # Saltos en cadena: una secuencia completa cuenta como un único movimiento/turno.
            jump_sequences = self._compute_jump_sequences(origin, occupied)
            for seq in jump_sequences:
                # seq incluye el origen como primer elemento
                if len(seq) >= 2:
                    moves.append(
                        Move(
                            pieza_id=pieza_id,
                            origen=origin,
                            destino=seq[-1],
                            sequence=seq,
                        )
                    )

            if self.allow_simple:
                for dest in self._compute_simple_moves(origin, occupied):
                    moves.append(Move(pieza_id=pieza_id, origen=origin, destino=dest))

        return moves

    def move(self, move: Move) -> None:
        # Si hay secuencia, mover directamente al destino final.
        self.positions[move.pieza_id] = move.destino
        self.last_move = move
        self.current_index = (self.current_index + 1) % len(self.players_order)

    def winner(self) -> Optional[str]:
        for player_id in self.players_order:
            target = self.target_by_player.get(player_id)
            if target is None:
                continue
            goal_positions = set(GOAL_POSITIONS.get(target, []))
            player_positions = [
                pos
                for pid, pos in self.positions.items()
                if self.piece_owner.get(pid) == player_id and pos
            ]
            if player_positions and all(pos in goal_positions for pos in player_positions):
                return player_id
        return None

    def _compute_simple_moves(self, origin_key: str, occupied_positions: Iterable[str]) -> List[str]:
        origin_coord = _axial_from_key(origin_key)
        if not origin_coord:
            return []
        occupied_set = set(occupied_positions)
        return [
            key
            for key in (
                _key_from_axial(origin_coord[0] + d["dq"], origin_coord[1] + d["dr"])
                for d in AXIAL_DIRECTIONS
            )
            if key and key not in occupied_set
        ]

    def _compute_jump_moves(self, origin_key: str, occupied_positions: Iterable[str]) -> List[str]:
        origin_coord = _axial_from_key(origin_key)
        if not origin_coord:
            return []

        occupied_set = set(occupied_positions)
        landings: List[str] = []
        for d in AXIAL_DIRECTIONS:
            middle_key = _key_from_axial(origin_coord[0] + d["dq"], origin_coord[1] + d["dr"])
            landing_key = _key_from_axial(origin_coord[0] + 2 * d["dq"], origin_coord[1] + 2 * d["dr"])
            if middle_key and landing_key and middle_key in occupied_set and landing_key not in occupied_set:
                landings.append(landing_key)

        return landings

    def _compute_jump_sequences(self, origin_key: str, occupied_positions: Iterable[str]) -> List[List[str]]:
        """Devuelve secuencias completas de saltos (origen ... landing_final)."""
        origin_coord = _axial_from_key(origin_key)
        if not origin_coord:
            return []

        occupied_set = set(occupied_positions)
        occupied_wo_origin = occupied_set - {origin_key}
        sequences: List[List[str]] = []

        def dfs(coord: Tuple[int, int], path: List[str], visited_landings: Set[str]) -> None:
            extended = False
            for d in AXIAL_DIRECTIONS:
                middle_key = _key_from_axial(coord[0] + d["dq"], coord[1] + d["dr"])
                landing_key = _key_from_axial(coord[0] + 2 * d["dq"], coord[1] + 2 * d["dr"])

                if not (middle_key and landing_key):
                    continue
                if middle_key not in occupied_set:
                    continue
                if landing_key in occupied_wo_origin:
                    continue
                if landing_key == origin_key:
                    continue
                if landing_key in visited_landings:
                    continue

                landing_coord = _axial_from_key(landing_key)
                if not landing_coord:
                    continue

                extended = True
                visited_landings.add(landing_key)
                dfs(landing_coord, path + [landing_key], visited_landings)
                visited_landings.remove(landing_key)

            if not extended and len(path) >= 2:
                sequences.append(path)

        dfs(origin_coord, [origin_key], set())
        return sequences


class MCTSAgent:
    def __init__(self, simulations: int = 10, rollout_depth: int = 21) -> None:
        self.simulations = simulations
        self.rollout_depth = rollout_depth

    def suggest_move(
        self,
        partida_id: str,
        jugador_id: str,
        allow_simple: bool = True,
        simulations: Optional[int] = None,
    ) -> Dict[str, object]:
        if not partida_id or not jugador_id:
            raise ValueError("partida_id y jugador_id son requeridos")

        # Seguridad extra: no sugerir si no es el turno del jugador.
        turno_actual = (
            Turno.objects.filter(partida_id=partida_id, fin__isnull=True)
            .order_by("numero")
            .first()
        )
        if turno_actual is None:
            raise ValueError("No hay un turno activo para la partida")
        if str(turno_actual.jugador_id) != str(jugador_id):
            raise ValueError("No es el turno de este jugador")

        # Obtener el estado actual del tablero desde la base de datos
        piezas = list(Pieza.objects.filter(partida_id=partida_id))
        if not piezas:
            raise ValueError("No hay piezas registradas para la partida")

        # Obtener el orden de los jugadores
        participaciones = list(
            JugadorPartida.objects.filter(partida_id=partida_id).order_by("orden_participacion")
        )
        if not participaciones:
            raise ValueError("No hay jugadores registrados en la partida")

        players_order = [str(p.jugador_id) for p in participaciones]
        try:
            current_index = players_order.index(str(jugador_id))
        except ValueError:
            raise ValueError("El jugador no participa en la partida")

        # Construir el estado para MCTS
        positions: Dict[str, str] = {p.id_pieza: p.posicion for p in piezas if p.posicion}
        piece_owner: Dict[str, str] = {p.id_pieza: str(p.jugador_id) for p in piezas}
        piece_type: Dict[str, str] = {p.id_pieza: p.tipo for p in piezas}
        
        target_by_player: Dict[str, int] = {}
        for p_id in players_order:
            pieza_jugador = next((p for p in piezas if str(p.jugador_id) == p_id and p.tipo), None)
            if pieza_jugador:
                punta = _parse_punta(pieza_jugador.tipo)
                target = _target_punta(punta)
                if target is not None:
                    target_by_player[p_id] = target

        initial_state = ChineseCheckersState(
            positions=positions,
            piece_owner=piece_owner,
            piece_type=piece_type,
            players_order=players_order,
            current_index=current_index,
            target_by_player=target_by_player,
            allow_simple=allow_simple,
        )

        # El agente solo puede mover sus propias piezas
        piezas_jugador_ids = {p.id_pieza for p in piezas if str(p.jugador_id) == str(jugador_id)}

        root_moves = [
            m for m in initial_state.get_possible_moves() 
            if m.pieza_id in piezas_jugador_ids
        ]
        if not root_moves:
            raise ValueError("No hay movimientos validos disponibles para el jugador actual")

        if len(root_moves) == 1:
            move = root_moves[0]
            return {
                "pieza_id": move.pieza_id,
                "origen": move.origen,
                "destino": move.destino,
                "heuristica": "mcts",
                "simulaciones": 0,
                "puntuacion": 0.0,
            }

        root = Node(initial_state)
        root.player_number = initial_state.current_index + 1

        montecarlo = MonteCarlo(root)

        def child_finder(node: Node, mc: MonteCarlo) -> None:
            moves = node.state.get_possible_moves()
            if node.state.current_player_id() == str(jugador_id):
                moves = [m for m in moves if m.pieza_id in piezas_jugador_ids]

            for move in moves:
                child_state = deepcopy(node.state)
                child_state.move(move)
                child = Node(child_state)
                child.player_number = child_state.current_index + 1
                node.add_child(child)

        def node_evaluator(node: Node, mc: MonteCarlo) -> float:
            winner = node.state.winner()
            if winner is not None:
                return 1.0 if winner == str(jugador_id) else -1.0

            rollout_state = deepcopy(node.state)
            for _ in range(self.rollout_depth):
                winner = rollout_state.winner()
                if winner is not None:
                    return 1.0 if winner == str(jugador_id) else -1.0

                moves = rollout_state.get_possible_moves()
                if rollout_state.current_player_id() == str(jugador_id):
                    moves = [m for m in moves if m.pieza_id in piezas_jugador_ids]

                if not moves:
                    return -1.0

                rollout_state.move(random.choice(moves))

            return 0.0

        montecarlo.child_finder = child_finder
        montecarlo.node_evaluator = node_evaluator

        requested_simulations = simulations if simulations is not None else self.simulations
        capped_simulations = min(requested_simulations, 6 + len(root_moves))
        montecarlo.simulate(capped_simulations)

        root_children = list(getattr(root, "children", []) or [])
        chosen_child: Optional[Node] = None
        if root_children:
            def _child_key(child: Node):
                return (
                    getattr(child, "visits", 0),
                    float(getattr(child, "win_value", 0.0)),
                )

            chosen_child = max(root_children, key=_child_key)

        if chosen_child is not None and getattr(chosen_child.state, "last_move", None) is not None:
            move = chosen_child.state.last_move
        else:
            move = random.choice(root_moves)

        # Verificación final: nunca devolver un movimiento con pieza ajena.
        if move.pieza_id not in piezas_jugador_ids:
            move = random.choice(root_moves)
        payload: Dict[str, object] = {
            "pieza_id": move.pieza_id,
            "origen": move.origen,
            "destino": move.destino,
            "heuristica": "mcts",
            "simulaciones": capped_simulations,
            "puntuacion": float(getattr(chosen_child, "win_value", 0.0)) if chosen_child else 0.0,
        }

        # Si es un salto en cadena, devolver también la secuencia paso a paso (como la heurística).
        if move.sequence and len(move.sequence) >= 2:
            payload["secuencia"] = [
                {"origen": move.sequence[i], "destino": move.sequence[i + 1]}
                for i in range(len(move.sequence) - 1)
            ]

        return payload
