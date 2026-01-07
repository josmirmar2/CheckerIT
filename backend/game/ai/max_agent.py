from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ..models import Movimiento, Pieza

# Pesos heurísticos (Max) visibles y ajustables
W_TOTAL_DIST = 1.0           # Distancia total de tus piezas a la meta (se resta)
W_FRONT_DIST = 0.6           # Distancia de la pieza más adelantada (se resta)
W_BLOCKED = 0.4              # Penalizar piezas sin movimientos
W_PROGRESS_ADV = 0.4         # Bono por acercar la pieza movida
W_PROGRESS_BACK = 0.8        # Penalización por alejar la pieza movida
W_JUMP_BONUS = 0.2           # Bono por salto
W_NOJUMP_PENALTY = 0.2       # Penalización por mover simple cuando existen saltos
W_CHAIN_LEN_BONUS = 0.15     # Bono extra por cada salto en cadena
W_REVERSE_PENALTY = 2.0      # Penaliza deshacer la última jugada (A->B seguido de B->A)
W_SAME_PIECE_PENALTY = 0.2   # Penaliza repetir con la misma pieza en turnos consecutivos
W_FAR_DESTINATION = 0.5      # Penaliza terminar lejos de la punta objetivo
W_HOME_PENALTY = 0.6         # Penaliza piezas estacionadas en su punta inicial
W_GOAL_MOVE_PENALTY = 1.2    # Penaliza mover piezas ya asentadas en la punta destino
W_WIN_MOVE_BONUS = 200.0     # Prioriza el movimiento que completa la victoria
W_GOAL_LANDING_PENALTY = 40.0  # Desincentiva ocupar la punta destino antes de cerrar la partida
W_LONE_PIECE_BONUS = 50.0      # Incentiva mover la única pieza fuera de la punta destino

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
    0: ['0-0', '1-1', '0-3', '1-3', '2-3', '0-1', '0-2', '1-2', '2-2', '3-3'],
    1: ['0-4', '2-4', '0-5', '2-5', '1-6', '1-4', '3-4', '1-5', '0-6', '0-7'],
    2: ['12-4', '10-4', '11-5', '9-5', '9-6', '11-4', '9-4', '10-5', '10-6', '9-7'],
    3: ['3-13', '1-13', '0-14', '2-14', '1-15', '2-13', '0-13', '1-14', '0-15', '0-16'],
    4: ['0-9', '0-11', '1-11', '0-12', '2-12', '0-10', '1-10', '2-11', '1-12', '3-12'],
    5: ['9-9', '9-11', '10-11', '10-12', '12-12', '9-10', '10-10', '11-11', '9-12', '11-12'],
}

TARGET_MAP = {0: 3, 3: 0, 1: 5, 5: 1, 2: 4, 4: 2}


@dataclass
class MoveCandidate:
    pieza_id: str
    origen: str
    destino: str
    score: float
    detail: Dict[str, float]
    sequence: Optional[List[str]] = None


def _axial_from_key(key: str) -> Optional[Tuple[int, int]]:
    # Convierte clave 'col-fila' a coordenadas axiales (q, r)
    coord = POSITION_TO_CARTESIAN.get(key)
    if not coord:
        return None
    return coord["q"], coord["r"]


def _key_from_axial(q: int, r: int) -> Optional[str]:
    # Convierte coordenadas axiales (q, r) a clave 'col-fila'
    return CARTESIAN_TO_POSITION.get(f"{q},{r}")


def _hex_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    # Distancia en hex grid usando la métrica máx de |dq|, |dr|, |ds|
    dq = a[0] - b[0]
    dr = a[1] - b[1]
    ds = dq + dr
    return max(abs(dq), abs(dr), abs(ds))


def _distance_to_goal(pos_key: Optional[str], target_punta: int) -> Optional[int]:
    # Distancia mínima desde una posición a cualquier casilla objetivo de la punta destino
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
    # Extrae el índice de punta desde el campo tipo (formato 'punta-color')
    try:
        return int(str(tipo).split('-')[0])
    except Exception:
        return None


def _target_punta(punta: Optional[int]) -> Optional[int]:
    # Mapea punta inicial a su punta objetivo
    if punta is None:
        return None
    return TARGET_MAP.get(punta)


class MaxHeuristicAgent:
    """
    Agente Max estilo "machine_move" (como el ejemplo de ajedrez):
    - Recorre todos los movimientos legales del jugador.
    - Evalúa cada movimiento con una función de evaluación heurística.
    - Se queda con el movimiento de mayor puntuación.
    """

    def suggest_move(
        self,
        partida_id: str,
        jugador_id: str,
        allow_simple: bool = True,
    ) -> Dict[str, object]:
        # 1) Validar entrada y obtener todas las piezas de la partida
        if not partida_id or not jugador_id:
            raise ValueError("partida_id y jugador_id son requeridos")

        piezas = list(Pieza.objects.filter(partida_id=partida_id))
        if not piezas:
            raise ValueError("No hay piezas registradas para la partida")

        # 2) Filtrar piezas del jugador y determinar punta objetivo
        piezas_jugador = [p for p in piezas if str(p.jugador_id) == str(jugador_id)]
        if not piezas_jugador:
            raise ValueError("El jugador no tiene piezas en la partida")

        punta = _parse_punta(piezas_jugador[0].tipo)
        target = _target_punta(punta)
        if target is None:
            raise ValueError("No se pudo determinar la punta objetivo para el jugador")

        # 3) Estado ocupado y detección de si hay algún salto posible
        occupied = {p.posicion for p in piezas if p.posicion}

        # Último movimiento del jugador (para evitar oscilaciones A->B->A)
        last_move = (
            Movimiento.objects.filter(partida_id=partida_id, jugador_id=jugador_id)
            .select_related("turno", "pieza")
            .order_by("-turno__numero", "-id_movimiento")
            .first()
        )
        last_from = getattr(last_move, "origen", None)
        last_to = getattr(last_move, "destino", None)
        last_piece_id = getattr(last_move, "pieza_id", None)

        # ¿Hay algún salto (cadena) disponible para este jugador en el estado actual?
        has_any_jump = any(
            self._compute_jump_sequences(p.posicion, occupied)
            for p in piezas_jugador
            if p.posicion
        )

        # 4) Puntuar el estado actual como referencia (base_score)
        base_score, _, _, _, _ = self._evaluate_state(
            ((p.id_pieza, str(p.jugador_id), p.tipo, p.posicion) for p in piezas),
            jugador_id,
            target,
            return_detail=True,
        )

        # 5) Estilo machine_move: evaluar cada movimiento y escoger el mejor
        best: Optional[MoveCandidate] = None

        for pieza in piezas_jugador:
            if not pieza.posicion:
                continue
            # 5.a) Obtener todos los movimientos válidos de la pieza
            simple_moves = set(self._compute_simple_moves(pieza.posicion, occupied)) if allow_simple else set()
            jump_sequences = self._compute_jump_sequences(pieza.posicion, occupied)
            jump_best = self._pick_best_jump_sequence(pieza.posicion, jump_sequences, target)

            # Candidatos: movimientos simples + (si existe) mejor salto en cadena
            candidates: List[Tuple[str, Optional[List[str]]]] = []
            for destino in sorted(simple_moves):
                candidates.append((destino, None))
            if jump_best is not None:
                candidates.append((jump_best[-1], jump_best))

            for destino, seq in candidates:
                # 5.b) Calcular score heurístico para este movimiento
                score, detail = self._score_after_move(
                    partida_id=partida_id,
                    jugador_id=jugador_id,
                    pieza_id=pieza.id_pieza,
                    origen=pieza.posicion,
                    destino=destino,
                    piezas=piezas,
                    target_punta=target,
                )
                is_jump = seq is not None
                jump_bonus = W_JUMP_BONUS if is_jump else 0.0
                chain_len = (len(seq) - 1) if seq else 0
                chain_bonus = float(chain_len) * W_CHAIN_LEN_BONUS
                non_jump_penalty = W_NOJUMP_PENALTY if has_any_jump and not is_jump else 0.0

                reverse_penalty = 0.0
                if last_from and last_to and last_from == destino and last_to == pieza.posicion:
                    reverse_penalty = W_REVERSE_PENALTY

                same_piece_penalty = W_SAME_PIECE_PENALTY if (last_piece_id and str(last_piece_id) == str(pieza.id_pieza)) else 0.0

                adjusted_score = score + jump_bonus + chain_bonus - non_jump_penalty - reverse_penalty - same_piece_penalty
                delta = adjusted_score - base_score

                detail.update({
                    "delta": delta,
                    "salto": is_jump,
                    "bonus_salto": jump_bonus,
                    "saltos_en_cadena": chain_len,
                    "bonus_cadena": chain_bonus,
                    "penalizacion_no_salto": non_jump_penalty,
                    "penalizacion_reverse": reverse_penalty,
                    "penalizacion_misma_pieza": same_piece_penalty,
                })

                # 5.c) Guardar el mejor movimiento (preferir salto en empate)
                if best is None or adjusted_score > best.score or (
                    adjusted_score == best.score and is_jump and not best.detail.get("salto", False)
                ):
                    best = MoveCandidate(
                        pieza_id=pieza.id_pieza,
                        origen=pieza.posicion,
                        destino=destino,
                        score=adjusted_score,
                        detail=detail,
                        sequence=seq,
                    )

        if best is None:
            raise ValueError("No hay movimientos validos disponibles")

        payload: Dict[str, object] = {
            "pieza_id": best.pieza_id,
            "origen": best.origen,
            "destino": best.destino,
            "heuristica": "max",
            "puntuacion": best.score,
            "detalle": {**best.detail, "base": base_score},
        }

        # Si es un salto en cadena, devolver también la secuencia paso a paso
        if best.sequence and len(best.sequence) >= 2:
            payload["secuencia"] = [
                {"origen": best.sequence[i], "destino": best.sequence[i + 1]}
                for i in range(len(best.sequence) - 1)
            ]

        return payload

    def _pick_best_jump_sequence(
        self,
        origin_key: str,
        sequences: List[List[str]],
        target_punta: int,
    ) -> Optional[List[str]]:
        """Escoge la mejor secuencia de salto priorizando llegar más lejos hacia la meta."""
        if not sequences:
            return None

        dist_before = _distance_to_goal(origin_key, target_punta)
        if dist_before is None:
            return max(sequences, key=lambda s: len(s))

        origin_axial = _axial_from_key(origin_key)

        def rank(seq: List[str]) -> Tuple[float, int, int]:
            final = seq[-1]
            dist_after = _distance_to_goal(final, target_punta)
            progress = float(dist_before - dist_after) if dist_after is not None else float("-inf")
            chain_len = len(seq) - 1
            travel = 0
            if origin_axial:
                final_axial = _axial_from_key(final)
                if final_axial:
                    travel = _hex_distance(origin_axial, final_axial)
            return (progress, chain_len, travel)

        return max(sequences, key=rank)

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
        """Evalúa el estado tras mover una pieza"""
        goal_positions: Set[str] = set()
        if target_punta is not None:
            goal_positions = set(GOAL_POSITIONS.get(target_punta, []))

        player_positions_before = [
            p.posicion for p in piezas if str(p.jugador_id) == str(jugador_id) and p.posicion
        ]
        outside_before = [pos for pos in player_positions_before if pos not in goal_positions]
        lone_piece_bonus = 0.0
        lone_piece_candidate = len(outside_before) == 1 and origen in outside_before

        # 1) Construir estado hipotético actualizado
        piezas_actualizadas: List[Tuple[str, str, str, str]] = []  # (pieza_id, jugador_id, tipo, posicion)
        for p in piezas:
            pos = destino if p.id_pieza == pieza_id else p.posicion
            piezas_actualizadas.append((p.id_pieza, str(p.jugador_id), p.tipo, pos))

        # 2) Evaluar el estado resultante (distancias y bloqueos)
        score, dist_total, min_distance, blocked, home_in_home = self._evaluate_state(
            piezas_actualizadas,
            jugador_id,
            target_punta,
            return_detail=True,
        )

        # 3) Añadir progreso de la pieza movida (acercar vs alejar)
        dist_before = _distance_to_goal(origen, target_punta)
        dist_after = _distance_to_goal(destino, target_punta)
        piece_progress = 0.0
        far_penalty = 0.0
        goal_move_penalty = 0.0
        win_bonus = 0.0
        goal_landing_penalty = 0.0
        if dist_before is not None and dist_after is not None:
            piece_progress = float(dist_before - dist_after)
            if piece_progress >= 0:
                score += W_PROGRESS_ADV * piece_progress
            else:
                score += W_PROGRESS_BACK * piece_progress
        if dist_after is not None:
            far_penalty = W_FAR_DESTINATION * float(dist_after)
            score -= far_penalty

        # Penalizar mover piezas que ya están dentro de la punta objetivo
        if goal_positions and origen in goal_positions:
            goal_move_penalty = W_GOAL_MOVE_PENALTY
            score -= goal_move_penalty

        player_positions_after = [
            pos for (_pid, _jug_id, _tipo, pos) in piezas_actualizadas
            if str(_jug_id) == str(jugador_id)
        ]
        outside_after = [pos for pos in player_positions_after if pos and pos not in goal_positions]

        if goal_positions and player_positions_after:
            if not outside_after:
                win_bonus = W_WIN_MOVE_BONUS
                score += win_bonus
            elif destino in goal_positions:
                goal_landing_penalty = W_GOAL_LANDING_PENALTY
                score -= goal_landing_penalty

        if lone_piece_candidate:
            lone_piece_bonus = W_LONE_PIECE_BONUS
            score += lone_piece_bonus

        detail = {
            "dist_total": dist_total,
            "dist_min": min_distance,
            "blocked": blocked,
            "en_punta_inicial": home_in_home,
            "dist_before": dist_before,
            "dist_after": dist_after,
            "progreso_pieza": piece_progress,
            "penalizacion_lejania": far_penalty,
            "penalizacion_meta": goal_move_penalty,
            "penalizacion_aterrizaje_meta": goal_landing_penalty,
            "bonus_victoria": win_bonus,
            "bonus_pieza_sola": lone_piece_bonus,
        }
        return score, detail

    def _evaluate_state(
        self,
        piezas: Iterable[Tuple[str, str, str, Optional[str]]],
        jugador_id: str,
        target_punta: int,
        return_detail: bool = False,
    ) -> float | Tuple[float, float, float, int]:
        """
        Heurística Max: menor distancia total y punta más adelantada, penaliza bloqueos, sólo evalúa el estado actual.
        """
        goal_positions = GOAL_POSITIONS.get(target_punta, [])
        goal_coords = [_axial_from_key(pos) for pos in goal_positions]
        goal_coords = [c for c in goal_coords if c is not None]
        if not goal_coords:
            return float("-inf") if not return_detail else (float("-inf"), float("inf"), float("inf"), 0, 0)

        total_distance = 0.0
        min_distance = None
        piezas_count = 0
        home_in_home = 0

        piezas_list = list(piezas)
        occupied = {pos for (_, jug_id, _tipo, pos) in piezas_list if pos}

        blocked = 0

        for _, jug_id, tipo, pos in piezas_list:
            # Saltar piezas de otros jugadores
            if str(jug_id) != str(jugador_id):
                continue
            punta = _parse_punta(tipo)
            if punta is None or not pos:
                continue
            axial = _axial_from_key(pos)
            if not axial:
                continue

            # Distancia mínima de esta pieza a la meta
            min_dist = min(_hex_distance(axial, goal) for goal in goal_coords)
            total_distance += float(min_dist)
            if min_distance is None or min_dist < min_distance:
                min_distance = min_dist
            piezas_count += 1

            # Penalización por seguir dentro de la punta inicial
            home_positions = GOAL_POSITIONS.get(punta, [])
            if pos in home_positions:
                home_in_home += 1

            # Bloqueos: piezas sin movimientos legales (permitimos simples y saltos)
            moves = self._get_valid_moves(pos, occupied, allow_simple=True)
            if len(moves) == 0:
                blocked += 1

        if piezas_count == 0:
            return float("-inf") if not return_detail else (float("-inf"), float("inf"), float("inf"), blocked, home_in_home)

        min_distance = float(min_distance if min_distance is not None else 0)

        # Puntuación: distancias y bloqueos (se restan porque son "costes")
        score = 0.0
        score -= W_TOTAL_DIST * float(total_distance)
        score -= W_FRONT_DIST * min_distance
        score -= W_BLOCKED * float(blocked)
        score -= W_HOME_PENALTY * float(home_in_home)

        if return_detail:
            return score, total_distance, min_distance, blocked, home_in_home
        return score

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

    def _compute_jump_sequences(self, origin_key: str, occupied_positions: Set[str]) -> List[List[str]]:
        """Devuelve secuencias completas de saltos (origen ... landing_final)."""
        origin_coord = _axial_from_key(origin_key)
        if not origin_coord:
            return []

        occupied_wo_origin = set(occupied_positions)
        occupied_wo_origin.discard(origin_key)

        sequences: List[List[str]] = []

        def dfs(coord: Tuple[int, int], path: List[str], visited_landings: Set[str]) -> None:
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
                if middle_key not in occupied_positions:
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
                sequences.append(path)

        dfs(origin_coord, [origin_key], set())
        return sequences
