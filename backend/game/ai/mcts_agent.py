from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import random
from typing import Dict, Iterable, List, Optional

from montecarlo.node import Node
from montecarlo.montecarlo import MonteCarlo

from ..models import JugadorPartida, Pieza
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

            if self.allow_simple:
                for dest in self._compute_simple_moves(origin, occupied):
                    moves.append(Move(pieza_id=pieza_id, origen=origin, destino=dest))

            for dest in self._compute_jump_moves(origin, occupied):
                moves.append(Move(pieza_id=pieza_id, origen=origin, destino=dest))

        return moves

    def move(self, move: Move) -> None:
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


class MCTSAgent:
    def __init__(self, simulations: int = 25, rollout_depth: int = 40) -> None:
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

        piezas = list(Pieza.objects.filter(partida_id=partida_id))
        if not piezas:
            raise ValueError("No hay piezas registradas para la partida")

        participaciones = list(
            JugadorPartida.objects.filter(partida_id=partida_id).order_by("orden_participacion")
        )
        if not participaciones:
            raise ValueError("No hay jugadores registrados en la partida")

        players_order = [str(p.jugador_id) for p in participaciones]
        if str(jugador_id) not in players_order:
            raise ValueError("El jugador no participa en la partida")

        positions: Dict[str, str] = {}
        piece_owner: Dict[str, str] = {}
        piece_type: Dict[str, str] = {}
        target_by_player: Dict[str, int] = {}

        for pieza in piezas:
            positions[pieza.id_pieza] = pieza.posicion
            piece_owner[pieza.id_pieza] = str(pieza.jugador_id)
            piece_type[pieza.id_pieza] = pieza.tipo

        for player_id in players_order:
            pieza_player = next((p for p in piezas if str(p.jugador_id) == player_id and p.tipo), None)
            punta = _parse_punta(pieza_player.tipo) if pieza_player else None
            target = _target_punta(punta)
            if target is None:
                raise ValueError("No se pudo determinar la punta objetivo para el jugador")
            target_by_player[player_id] = target

        current_index = players_order.index(str(jugador_id))
        state = ChineseCheckersState(
            positions=positions,
            piece_owner=piece_owner,
            piece_type=piece_type,
            players_order=players_order,
            current_index=current_index,
            target_by_player=target_by_player,
            allow_simple=allow_simple,
        )

        root_moves = state.get_possible_moves()
        if not root_moves:
            raise ValueError("No hay movimientos validos disponibles")

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

        root = Node(state)
        root.player_number = current_index + 1

        montecarlo = MonteCarlo(root)

        def child_finder(node: Node, mc: MonteCarlo) -> None:
            moves = node.state.get_possible_moves()
            for move in moves:
                child_state = deepcopy(node.state)
                child_state.move(move)
                child_state.last_move = move
                child = Node(child_state)
                child.player_number = child_state.current_index + 1
                node.add_child(child)

        def node_evaluator(node: Node, mc: MonteCarlo) -> float:
            winner = node.state.winner()
            if winner is not None:
                current_player = node.state.current_player_id()
                return 1.0 if winner == current_player else -1.0

            rollout_state = deepcopy(node.state)
            max_rollout_depth = self.rollout_depth

            for _ in range(max_rollout_depth):
                winner = rollout_state.winner()
                if winner is not None:
                    current_player = node.state.current_player_id()
                    return 1.0 if winner == current_player else -1.0

                moves = rollout_state.get_possible_moves()
                if not moves:
                    return -1.0

                move = random.choice(moves)
                rollout_state.move(move)

            return 0.0

        montecarlo.child_finder = child_finder
        montecarlo.node_evaluator = node_evaluator

        requested_simulations = simulations if simulations is not None else self.simulations
        capped_simulations = min(requested_simulations, 10 + 2 * len(root_moves))
        montecarlo.simulate(capped_simulations)

        chosen = None
        root_children = list(getattr(root, "children", []) or [])
        if root_children:
            def _child_key(child):
                return (
                    getattr(child, "visits", 0),
                    getattr(child, "win_value", 0.0),
                )
            chosen = max(root_children, key=_child_key)
        else:
            chosen = montecarlo.make_choice()

        if not chosen or not getattr(chosen.state, "last_move", None):
            raise ValueError("No hay movimientos validos disponibles")

        move = chosen.state.last_move
        if str(piece_owner.get(move.pieza_id)) != str(jugador_id):
            move = root_moves[0]
        payload: Dict[str, object] = {
            "pieza_id": move.pieza_id,
            "origen": move.origen,
            "destino": move.destino,
            "heuristica": "mcts",
            "simulaciones": capped_simulations,
            "puntuacion": float(getattr(chosen, "win_value", 0.0)) if chosen else 0.0,
        }

        return payload
