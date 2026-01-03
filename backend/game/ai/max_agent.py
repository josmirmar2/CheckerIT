from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ..models import Pieza

CARTESIAN_COORD_ROWS: List[List[Dict[str, int]]] = [
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

POSITION_TO_CARTESIAN: Dict[str, Dict[str, int]] = {}
CARTESIAN_TO_POSITION: Dict[str, str] = {}
for row_idx, row in enumerate(CARTESIAN_COORD_ROWS):
    for col_idx, coord in enumerate(row):
        key = f"{col_idx}-{row_idx}"
        POSITION_TO_CARTESIAN[key] = coord
        CARTESIAN_TO_POSITION[f"{coord['q']},{coord['r']}"] = key

AXIAL_DIRECTIONS: List[Dict[str, int]] = [
    {"dq": 1, "dr": 0},
    {"dq": -1, "dr": 0},
    {"dq": 0, "dr": 1},
    {"dq": 0, "dr": -1},
    {"dq": 1, "dr": -1},
    {"dq": -1, "dr": 1},
]

GOAL_POSITIONS: Dict[int, List[str]] = {
    0: ['3-13', '1-13', '0-14', '2-14', '1-15', '2-13', '0-13', '1-14', '0-15', '0-16'],  # punta 3
    1: ['9-9', '9-11', '10-11', '10-12', '12-12', '9-10', '10-10', '11-11', '9-12', '11-12'],  # punta 5
    2: ['0-9', '0-11', '1-11', '0-12', '2-12', '0-10', '1-10', '2-11', '1-12', '3-12'],  # punta 4
    3: ['0-0', '1-1', '0-3', '1-3', '2-3', '0-1', '0-2', '1-2', '2-2', '3-3'],  # punta 0
    4: ['12-4', '10-4', '11-5', '9-5', '9-6', '11-4', '9-4', '10-5', '10-6', '9-7'],  # punta 2
    5: ['0-4', '2-4', '0-5', '2-5', '1-6', '1-4', '3-4', '1-5', '0-6', '0-7'],  # punta 1
}

TARGET_MAP = {0: 3, 3: 0, 1: 5, 5: 1, 2: 4, 4: 2}


@dataclass
class MoveCandidate:
    pieza_id: str
    origen: str
    destino: str
    score: float
    detail: Dict[str, float]


def _axial_from_key(key: str) -> Optional[Tuple[int, int]]:
    coord = POSITION_TO_CARTESIAN.get(key)
    if not coord:
        return None
    return coord["q"], coord["r"]


def _key_from_axial(q: int, r: int) -> Optional[str]:
    return CARTESIAN_TO_POSITION.get(f"{q},{r}")


def _hex_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    dq = a[0] - b[0]
    dr = a[1] - b[1]
    ds = dq + dr
    return max(abs(dq), abs(dr), abs(ds))


def _distance_to_goal(pos_key: Optional[str], target_punta: int) -> Optional[int]:
    if not pos_key:
        return None
    axial = _axial_from_key(pos_key)
    if not axial:
        return None
    goals = GOAL_POSITIONS.get(target_punta, [])
    goal_coords = [_axial_from_key(g) for g in goals]
    goal_coords = [c for c in goal_coords if c]
    if not goal_coords:
        return None
    return min(_hex_distance(axial, g) for g in goal_coords)


def _parse_punta(tipo: str) -> Optional[int]:
    try:
        return int(str(tipo).split('-')[0])
    except Exception:
        return None


def _target_punta(punta: Optional[int]) -> Optional[int]:
    if punta is None:
        return None
    return TARGET_MAP.get(punta)


class MaxHeuristicAgent:
    """Agente base que elige el movimiento con mayor puntuacion heuristica (Max)."""

    def suggest_move(
        self,
        partida_id: str,
        jugador_id: str,
        allow_simple: bool = True,
    ) -> Dict[str, object]:
        if not partida_id or not jugador_id:
            raise ValueError("partida_id y jugador_id son requeridos")

        piezas = list(Pieza.objects.filter(partida_id=partida_id))
        if not piezas:
            raise ValueError("No hay piezas registradas para la partida")

        piezas_jugador = [p for p in piezas if str(p.jugador_id) == str(jugador_id)]
        if not piezas_jugador:
            raise ValueError("El jugador no tiene piezas en la partida")

        punta = _parse_punta(piezas_jugador[0].tipo)
        target = _target_punta(punta)
        if target is None:
            raise ValueError("No se pudo determinar la punta objetivo para el jugador")

        occupied = {p.posicion for p in piezas if p.posicion}
        base_score = self._evaluate_state(
            ((p.id_pieza, str(p.jugador_id), p.tipo, p.posicion) for p in piezas),
            jugador_id,
            target,
        )
        best: Optional[MoveCandidate] = None

        for pieza in piezas_jugador:
            if not pieza.posicion:
                continue
            movimientos = self._get_valid_moves(pieza.posicion, occupied, allow_simple)
            for destino in movimientos:
                score, detail = self._score_after_move(
                    partida_id=partida_id,
                    jugador_id=jugador_id,
                    pieza_id=pieza.id_pieza,
                    origen=pieza.posicion,
                    destino=destino,
                    piezas=piezas,
                    target_punta=target,
                )
                delta = score - base_score
                is_jump = destino not in self._compute_simple_moves(pieza.posicion, occupied)
                detail["delta"] = delta
                detail["salto"] = is_jump
                # Solo aceptar movimientos que mejoren la heuristica; si ninguno mejora, aceptar el "menos malo" para evitar bloqueo
                if score <= base_score and best is not None and best.score > base_score:
                    continue
                if best is None:
                    best = MoveCandidate(
                        pieza_id=pieza.id_pieza,
                        origen=pieza.posicion,
                        destino=destino,
                        score=score + (0.1 if is_jump else 0.0),
                        detail=detail,
                    )
                    continue

                # Preferir: (1) mejor score, (2) salto, (3) mayor delta de mejora
                current_score = score + (0.1 if is_jump else 0.0)
                best_is_jump = best.detail.get("salto", False)
                best_score = best.score
                best_delta = best.detail.get("delta", 0.0)

                if (
                    current_score > best_score
                    or (current_score == best_score and is_jump and not best_is_jump)
                    or (current_score == best_score and is_jump == best_is_jump and delta > best_delta)
                ):
                    best = MoveCandidate(
                        pieza_id=pieza.id_pieza,
                        origen=pieza.posicion,
                        destino=destino,
                        score=current_score,
                        detail=detail,
                    )

        if best is None:
            raise ValueError("No hay movimientos validos disponibles")

        return {
            "pieza_id": best.pieza_id,
            "origen": best.origen,
            "destino": best.destino,
            "heuristica": "max",
            "puntuacion": best.score,
            "detalle": {**best.detail, "base": base_score},
        }

    def _score_after_move(
        self,
        partida_id: str,
        jugador_id: str,
        pieza_id: str,
        origen: str,
        destino: str,
        piezas: List[Pieza],
        target_punta: int,
    ) -> Tuple[float, Dict[str, float]]:
        piezas_actualizadas: List[Tuple[str, str, str, str]] = []  # (pieza_id, jugador_id, tipo, posicion)
        for p in piezas:
            pos = destino if p.id_pieza == pieza_id else p.posicion
            piezas_actualizadas.append((p.id_pieza, str(p.jugador_id), p.tipo, pos))

        score = self._evaluate_state(piezas_actualizadas, jugador_id, target_punta)

        # Bonus/penalización por progreso individual de la pieza movida
        # Avanzar recibe bono moderado; retroceder recibe fuerte penalización
        dist_before = _distance_to_goal(origen, target_punta)
        dist_after = _distance_to_goal(destino, target_punta)
        piece_progress = 0.0
        if dist_before is not None and dist_after is not None:
            piece_progress = float(dist_before - dist_after)
            if piece_progress >= 0:
                # Bonus por avanzar
                score += 0.3 * piece_progress
            else:
                # Fuerte penalización por retroceder
                score += 0.8 * piece_progress

        detail = {
            "dist_total": -(score - 0.2 * piece_progress),
            "dist_before": dist_before,
            "dist_after": dist_after,
            "progreso_pieza": piece_progress,
        }
        return score, detail

    def _evaluate_state(
        self,
        piezas: Iterable[Tuple[str, str, str, Optional[str]]],
        jugador_id: str,
        target_punta: int,
    ) -> float:
        goal_positions = GOAL_POSITIONS.get(target_punta, [])
        goal_coords = [_axial_from_key(pos) for pos in goal_positions]
        goal_coords = [c for c in goal_coords if c is not None]
        if not goal_coords:
            return float("-inf")

        total_distance = 0
        min_distance = None
        piezas_count = 0

        for _, jug_id, tipo, pos in piezas:
            if str(jug_id) != str(jugador_id):
                continue
            punta = _parse_punta(tipo)
            if punta is None:
                continue
            if not pos:
                continue
            axial = _axial_from_key(pos)
            if not axial:
                continue
            min_dist = min(_hex_distance(axial, goal) for goal in goal_coords)
            total_distance += min_dist
            if min_distance is None or min_dist < min_distance:
                min_distance = min_dist
            piezas_count += 1

        if piezas_count == 0:
            return float("-inf")

        # Heuristica Max: minimizar distancia total y también premiar tener una pieza muy adelantada
        # score = -(dist_total) - 0.5*(dist_min)
        min_distance = min_distance if min_distance is not None else 0
        return -float(total_distance) - 0.5 * float(min_distance)

    def _get_valid_moves(
        self,
        origin_key: str,
        occupied_positions: Set[str],
        allow_simple: bool,
    ) -> List[str]:
        simple = self._compute_simple_moves(origin_key, occupied_positions) if allow_simple else []
        jumps = self._compute_jump_moves(origin_key, occupied_positions)
        return list({*simple, *jumps})

    def _compute_simple_moves(self, origin_key: str, occupied_positions: Set[str]) -> List[str]:
        origin_coord = _axial_from_key(origin_key)
        if not origin_coord:
            return []

        moves: List[str] = []
        for direction in AXIAL_DIRECTIONS:
            neighbor_q = origin_coord[0] + direction["dq"]
            neighbor_r = origin_coord[1] + direction["dr"]
            neighbor_key = _key_from_axial(neighbor_q, neighbor_r)
            if neighbor_key and neighbor_key not in occupied_positions:
                moves.append(neighbor_key)
        return moves

    def _compute_jump_moves(self, origin_key: str, occupied_positions: Set[str]) -> List[str]:
        origin_coord = _axial_from_key(origin_key)
        if not origin_coord:
            return []

        landings: Set[str] = set()

        def dfs(coord: Tuple[int, int]) -> None:
            for direction in AXIAL_DIRECTIONS:
                middle_q = coord[0] + direction["dq"]
                middle_r = coord[1] + direction["dr"]
                landing_q = coord[0] + 2 * direction["dq"]
                landing_r = coord[1] + 2 * direction["dr"]

                middle_key = _key_from_axial(middle_q, middle_r)
                landing_key = _key_from_axial(landing_q, landing_r)

                if not middle_key or not landing_key:
                    continue
                if middle_key not in occupied_positions:
                    continue
                if landing_key in occupied_positions:
                    continue
                if landing_key in landings:
                    continue

                landings.add(landing_key)
                dfs((landing_q, landing_r))

        dfs(origin_coord)
        return list(landings)
