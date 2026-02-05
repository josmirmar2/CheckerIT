from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from montecarlo.montecarlo import MonteCarlo
from montecarlo.node import Node

from ..models import JugadorPartida, Movimiento, Pieza, Turno
from .max_agent import (AXIAL_DIRECTIONS,GOAL_POSITIONS,POSITION_TO_CARTESIAN,_axial_from_key,_distance_to_goal,_key_from_axial,_parse_punta,_target_punta)


@dataclass(frozen=True)
class TurnMove:
    pieza_id: str
    sequence: Tuple[str, ...]  # incluye origen y destinos intermedios; último es destino final

    @property
    def origen(self) -> str:
        return self.sequence[0]

    @property
    def destino(self) -> str:
        return self.sequence[-1]


@dataclass(frozen=True)
class _PieceTuple:
    pieza_id: str
    jugador_id: str
    tipo: str
    posicion: str


@dataclass(frozen=True)
class GameState:
    """Estado inmutable para MCTS: una acción = un turno (simple o cadena de saltos)."""

    player_order: Tuple[str, ...]
    current_player_index: int
    player_targets: Tuple[Tuple[str, int], ...]  # (jugador_id, target_punta)
    pieces: Tuple[_PieceTuple, ...]

    @property
    def current_player_id(self) -> str:
        return self.player_order[self.current_player_index]

    def _target_for(self, jugador_id: str) -> Optional[int]:
        for jid, target in self.player_targets:
            if jid == jugador_id:
                return target
        return None

    def occupied(self) -> frozenset[str]:
        return frozenset(p.posicion for p in self.pieces if p.posicion)

    def piece_by_id(self) -> Dict[str, _PieceTuple]:
        return {p.pieza_id: p for p in self.pieces}

    def pieces_of(self, jugador_id: str) -> List[_PieceTuple]:
        return [p for p in self.pieces if p.jugador_id == jugador_id and p.posicion]

    def is_win(self, jugador_id: str) -> bool:
        target = self._target_for(jugador_id)
        if target is None:
            return False
        goal = set(GOAL_POSITIONS.get(target, []))
        ps = self.pieces_of(jugador_id)
        return bool(ps) and all(p.posicion in goal for p in ps)

    def any_winners(self) -> List[str]:
        winners: List[str] = []
        for jid in self.player_order:
            if self.is_win(jid):
                winners.append(jid)
        return winners

    def evaluate(self, root_player_id: str) -> float:
        winners = self.any_winners()
        if winners:
            if root_player_id in winners:
                return 1.0
            return -1.0

        totals: Dict[str, float] = {}
        for jid in self.player_order:
            target = self._target_for(jid)
            if target is None:
                continue
            total = 0.0
            for p in self.pieces_of(jid):
                d = _distance_to_goal(p.posicion, target)
                if d is None:
                    continue
                total += float(d)
            totals[jid] = total

        my_total = totals.get(root_player_id, 0.0)
        others = [v for k, v in totals.items() if k != root_player_id]
        if not others:
            return 0.0
        other_avg = sum(others) / float(len(others))
        denom = other_avg + my_total + 1e-6
        # cuanto menor es my_total respecto a otros, mejor
        score = (other_avg - my_total) / denom
        return max(-1.0, min(1.0, score))

    def apply(self, move: TurnMove) -> "GameState":
        pieces_list = list(self.pieces)
        for idx, p in enumerate(pieces_list):
            if p.pieza_id == move.pieza_id:
                pieces_list[idx] = _PieceTuple(
                    pieza_id=p.pieza_id,
                    jugador_id=p.jugador_id,
                    tipo=p.tipo,
                    posicion=move.destino,
                )
                break

        next_index = (self.current_player_index + 1) % len(self.player_order)
        return GameState(
            player_order=self.player_order,
            current_player_index=next_index,
            player_targets=self.player_targets,
            pieces=tuple(pieces_list),
        )


@dataclass(frozen=True)
class _LibState:
    """Estado usado por la librería imparaai-montecarlo.

    - `game` guarda el estado de juego inmutable.
    - `last_move` representa la acción que nos llevó hasta aquí (para reconstruir la jugada elegida).
    """

    game: GameState
    last_move: Optional[TurnMove] = None

    def apply(self, move: TurnMove) -> "_LibState":
        return _LibState(game=self.game.apply(move), last_move=move)


def _simple_moves(origin_key: str, occupied: frozenset[str]) -> List[str]:
    origin_coord = POSITION_TO_CARTESIAN.get(origin_key)
    if not origin_coord:
        return []
    moves: List[str] = []
    for d in AXIAL_DIRECTIONS:
        nq = origin_coord["q"] + d["dq"]
        nr = origin_coord["r"] + d["dr"]
        nk = _key_from_axial(nq, nr)
        if nk and nk not in occupied:
            moves.append(nk)
    return moves


def _jump_sequences(origin_key: str, occupied: frozenset[str]) -> List[Tuple[str, ...]]:
    origin_coord = _axial_from_key(origin_key)
    if not origin_coord:
        return []

    occupied_wo_origin = set(occupied)
    occupied_wo_origin.discard(origin_key)

    sequences: List[Tuple[str, ...]] = []

    def dfs(coord: Tuple[int, int], path: List[str], visited_landings: set[str]) -> None:
        extended = False
        for direction in AXIAL_DIRECTIONS:
            middle_q = coord[0] + direction["dq"]
            middle_r = coord[1] + direction["dr"]
            landing_q = coord[0] + 2 * direction["dq"]
            landing_r = coord[1] + 2 * direction["dr"]

            middle_key = _key_from_axial(middle_q, middle_r)
            landing_key = _key_from_axial(landing_q, landing_r)

            if not middle_key or not landing_key:
                continue
            if middle_key not in occupied:
                continue
            if landing_key in occupied_wo_origin:
                continue
            if landing_key == origin_key:
                continue
            if landing_key in visited_landings:
                continue

            extended = True
            visited_landings.add(landing_key)
            dfs((landing_q, landing_r), path + [landing_key], visited_landings)
            visited_landings.remove(landing_key)

        if not extended and len(path) >= 2:
            sequences.append(tuple(path))

    dfs(origin_coord, [origin_key], set())
    return sequences


def _rank_moves(
    moves: Iterable[TurnMove],
    state: GameState,
    jugador_id: str,
) -> List[TurnMove]:
    target = state._target_for(jugador_id)
    if target is None:
        return list(moves)

    def key(m: TurnMove) -> Tuple[float, int]:
        before = _distance_to_goal(m.origen, target) or 0
        after = _distance_to_goal(m.destino, target) or 0
        progress = float(before - after)
        chain = len(m.sequence) - 1
        return (progress, chain)

    return sorted(moves, key=key, reverse=True)


def legal_turn_moves(
    state: GameState,
    jugador_id: str,
    allow_simple: bool,
    max_moves: int = 60,
) -> List[TurnMove]:
    occupied = state.occupied()
    all_moves: List[TurnMove] = []

    for piece in state.pieces_of(jugador_id):
        if allow_simple:
            for dest in _simple_moves(piece.posicion, occupied):
                all_moves.append(TurnMove(pieza_id=piece.pieza_id, sequence=(piece.posicion, dest)))

        for seq in _jump_sequences(piece.posicion, occupied):
            all_moves.append(TurnMove(pieza_id=piece.pieza_id, sequence=seq))

    ranked = _rank_moves(all_moves, state, jugador_id)
    return ranked[:max_moves]


class MCTSAgent:
    """IA 'Difícil' basada en MCTS, compatible con el backend actual."""

    def suggest_move(
        self,
        partida_id: str,
        jugador_id: str,
        allow_simple: bool = True,
        iterations: int = 250,
        rollout_depth: int = 10,
        exploration: float = 1.35,
        seed: Optional[int] = None,
    ) -> Dict[str, object]:
        if not partida_id or not jugador_id:
            raise ValueError("partida_id y jugador_id son requeridos")

        # Turno activo debe corresponder al jugador
        turno_actual = (
            Turno.objects.filter(partida_id=partida_id, fin__isnull=True)
            .order_by("numero")
            .first()
        )
        if not turno_actual:
            raise ValueError("No hay turno activo para la partida")
        if str(turno_actual.jugador_id) != str(jugador_id):
            raise ValueError("No es el turno de este jugador")

        piezas = list(Pieza.objects.filter(partida_id=partida_id))
        if not piezas:
            raise ValueError("No hay piezas registradas para la partida")

        piezas_jugador = [p for p in piezas if str(p.jugador_id) == str(jugador_id) and p.posicion]
        if not piezas_jugador:
            raise ValueError("El jugador no tiene piezas en la partida")

        participaciones = list(
            JugadorPartida.objects.filter(partida_id=partida_id).order_by("orden_participacion")
        )
        player_order = tuple(str(p.jugador_id) for p in participaciones)
        if not player_order:
            # fallback mínimo
            player_order = tuple(sorted({str(p.jugador_id) for p in piezas if p.jugador_id}))

        try:
            current_index = player_order.index(str(jugador_id))
        except ValueError:
            current_index = 0

        # objetivo por jugador (según el tipo de sus piezas)
        targets: List[Tuple[str, int]] = []
        seen: set[str] = set()
        for p in piezas:
            jid = str(p.jugador_id)
            if jid in seen:
                continue
            seen.add(jid)
            punta = _parse_punta(p.tipo)
            target = _target_punta(punta)
            if target is not None:
                targets.append((jid, int(target)))

        piece_tuples = tuple(
            _PieceTuple(
                pieza_id=str(p.id_pieza),
                jugador_id=str(p.jugador_id),
                tipo=str(p.tipo),
                posicion=str(p.posicion),
            )
            for p in piezas
            if p.posicion
        )

        root_state = GameState(
            player_order=player_order,
            current_player_index=current_index,
            player_targets=tuple(targets),
            pieces=piece_tuples,
        )

        # La librería usa el módulo random global internamente.
        if seed is not None:
            random.seed(seed)

        root_moves = legal_turn_moves(root_state, root_state.current_player_id, allow_simple=allow_simple)
        if not root_moves:
            raise ValueError("No hay movimientos válidos disponibles")

        root_lib_state = _LibState(game=root_state, last_move=None)
        root_node = Node(root_lib_state)
        root_node.player_number = root_state.current_player_id

        montecarlo = MonteCarlo(root_node)

        def child_finder(node: Node, _mc: MonteCarlo) -> None:
            state: _LibState = node.state
            current_player = state.game.current_player_id
            # Para el nodo raíz respetamos allow_simple del endpoint; en el resto de turnos permitimos simples.
            allow_simple_local = allow_simple if node is montecarlo.root_node else True

            moves = legal_turn_moves(state.game, current_player, allow_simple=allow_simple_local)
            for move in moves:
                child_state = state.apply(move)
                child = Node(child_state)
                child.player_number = child_state.game.current_player_id
                node.add_child(child)

        def node_evaluator(node: Node, _mc: MonteCarlo) -> float:
            state: _LibState = node.state
            # Valor siempre desde la perspectiva del jugador raíz (la librería invierte en turnos rivales).
            return float(state.game.evaluate(root_player_id=str(jugador_id)))

        montecarlo.child_finder = child_finder
        montecarlo.node_evaluator = node_evaluator

        montecarlo.simulate(max(1, int(iterations)))

        chosen_child = montecarlo.make_choice()
        chosen_move = getattr(chosen_child.state, "last_move", None)
        if chosen_move is None:
            chosen_move = root_moves[0]

        payload: Dict[str, object] = {
            "pieza_id": chosen_move.pieza_id,
            "origen": chosen_move.origen,
            "destino": chosen_move.destino,
            "heuristica": "mcts",
            "simulaciones": int(iterations),
        }
        if len(chosen_move.sequence) >= 2:
            payload["secuencia"] = [
                {"origen": chosen_move.sequence[i], "destino": chosen_move.sequence[i + 1]}
                for i in range(len(chosen_move.sequence) - 1)
            ]

        # valor esperado (informativo): promedio de win_value/visits del hijo elegido
        if getattr(chosen_child, "visits", 0):
            payload["puntuacion"] = float(chosen_child.win_value / float(chosen_child.visits))

        # anti-oscillación leve: evita deshacer el último movimiento si hay alternativas
        last_move = (
            Movimiento.objects.filter(partida_id=partida_id, jugador_id=jugador_id)
            .select_related("turno", "pieza")
            .order_by("-turno__numero", "-id_movimiento")
            .first()
        )
        if last_move and chosen_move.sequence == (str(last_move.destino), str(last_move.origen)):
            for alt in root_moves[1:]:
                if alt.sequence != (str(last_move.destino), str(last_move.origen)):
                    payload["pieza_id"] = alt.pieza_id
                    payload["origen"] = alt.origen
                    payload["destino"] = alt.destino
                    payload["secuencia"] = [
                        {"origen": alt.sequence[i], "destino": alt.sequence[i + 1]}
                        for i in range(len(alt.sequence) - 1)
                    ]
                    break

        return payload
