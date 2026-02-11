from __future__ import annotations

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = next((p for p in CURRENT_FILE.parents if (p / "manage.py").exists()), None)
if BACKEND_DIR is None:
    raise RuntimeError("No se pudo localizar el directorio 'backend' (manage.py) para inicializar sys.path")
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "checkerit.settings")

import django    

django.setup()    

from django.db import transaction    
from django.utils import timezone    

from game.ai.max_agent import MaxHeuristicAgent, _distance_to_goal, _parse_punta, _target_punta    
from game.ai.mcts_agent import MCTSAgent    
from game.models import IA, Jugador, JugadorPartida, Movimiento, Partida, Pieza, Turno    
from game.views import get_occupied_positions, validate_move    


PUNTAS_ACTIVAS_MAP = {
    2: [0, 3],
    3: [0, 4, 5],
    4: [1, 2, 4, 5],
    6: [0, 1, 2, 3, 4, 5],
}

POSICIONES_POR_PUNTA = {
    0: ["0-0", "0-1", "1-1", "0-2", "1-2", "2-2", "0-3", "1-3", "2-3", "3-3"],
    1: ["0-4", "0-5", "1-4", "1-5", "1-6", "2-4", "2-5", "3-4", "0-6", "0-7"],
    2: ["12-4", "9-6", "11-4", "11-5", "10-6", "10-4", "10-5", "9-5", "9-4", "9-7"],
    3: ["3-13", "2-13", "2-14", "1-13", "1-14", "1-15", "0-13", "0-14", "0-15", "0-16"],
    4: ["0-9", "0-10", "2-12", "1-10", "1-11", "3-12", "2-11", "1-12", "0-11", "0-12"],
    5: ["9-9", "9-10", "11-11", "10-10", "10-11", "10-12", "12-12", "11-12", "9-11", "9-12"],
}

COLORES_POR_PUNTA = {
    0: "Blanco",
    1: "Azul",
    2: "Verde",
    3: "Negro",
    4: "Rojo",
    5: "Amarillo",
}


def _new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().timestamp()}"


def _print_header(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def _iter_steps_from_payload(payload: dict) -> Iterable[Tuple[str, str]]:
    secuencia = payload.get("secuencia")
    if isinstance(secuencia, list) and secuencia:
        for step in secuencia:
            yield str(step.get("origen")), str(step.get("destino"))
        return
    yield str(payload.get("origen")), str(payload.get("destino"))


def _apply_step_to_occupied(occupied: set[str], origin: str, dest: str) -> None:
    occupied.discard(str(origin))
    occupied.add(str(dest))


def _player_target(partida_id: str, jugador_id: str) -> Optional[int]:
    pieza = (
        Pieza.objects.filter(partida_id=partida_id, jugador_id=jugador_id)
        .exclude(posicion__isnull=True)
        .first()
    )
    if not pieza:
        return None
    punta = _parse_punta(str(pieza.tipo))
    return _target_punta(punta)


def _total_distance_to_goal(partida_id: str, jugador_id: str) -> float:
    target = _player_target(partida_id, jugador_id)
    if target is None:
        return 0.0
    total = 0.0
    for p in Pieza.objects.filter(partida_id=partida_id, jugador_id=jugador_id).exclude(posicion__isnull=True):
        d = _distance_to_goal(str(p.posicion), int(target))
        if d is not None:
            total += float(d)
    return total


def _pieces_in_goal(partida_id: str, jugador_id: str) -> int:
    target = _player_target(partida_id, jugador_id)
    if target is None:
        return 0
    # GOAL_POSITIONS está en max_agent, pero aquí no necesitamos el set exacto; basta con contar d==0? No.
    # Usamos distancia 0 como pertenencia a alguna casilla meta.
    count = 0
    for p in Pieza.objects.filter(partida_id=partida_id, jugador_id=jugador_id).exclude(posicion__isnull=True):
        d = _distance_to_goal(str(p.posicion), int(target))
        if d == 0:
            count += 1
    return count


def _initialize_pieces_for_player(partida: Partida, jugador: Jugador, orden_participacion: int) -> int:
    puntas_activas = PUNTAS_ACTIVAS_MAP.get(int(partida.numero_jugadores), [0, 3])
    punta_asignada = puntas_activas[int(orden_participacion) - 1]
    color = COLORES_POR_PUNTA.get(int(punta_asignada), "")
    posiciones = POSICIONES_POR_PUNTA.get(int(punta_asignada), POSICIONES_POR_PUNTA[0])

    for i, pos in enumerate(posiciones[:10]):
        Pieza.objects.create(
            id_pieza=f"P_{jugador.id_jugador}_{i}_{partida.id_partida}",
            tipo=f"{punta_asignada}-{color}",
            posicion=pos,
            jugador=jugador,
            partida=partida,
        )

    return int(punta_asignada)


@dataclass
class PlayerStats:
    jugador_id: str
    label: str
    moves: int = 0
    chains: int = 0
    chain_steps: int = 0
    invalid_moves: int = 0
    total_dist_start: float = 0.0
    total_dist_end: float = 0.0
    progress_sum: float = 0.0  # suma (dist_before - dist_after) en sus turnos
    in_goal_end: int = 0

    @property
    def avg_progress_per_move(self) -> float:
        return self.progress_sum / float(self.moves) if self.moves else 0.0

    @property
    def delta_total_dist(self) -> float:
        return self.total_dist_start - self.total_dist_end


@dataclass
class MatchResult:
    turns: int
    heuristic: PlayerStats
    mcts: PlayerStats

    def winner_by_distance(self) -> str:
        # "mejor" = mayor reducción de distancia total
        if self.heuristic.delta_total_dist > self.mcts.delta_total_dist:
            return "heuristica"
        if self.mcts.delta_total_dist > self.heuristic.delta_total_dist:
            return "mcts"
        return "empate"


def _make_turn(partida: Partida, numero: int, jugador: Jugador) -> Turno:
    return Turno.objects.create(
        id_turno=f"T{numero}_{partida.id_partida}",
        jugador=jugador,
        numero=numero,
        partida=partida,
        inicio=timezone.now(),
    )


def run_match(turns: int, iterations_mcts: int, seed_base: int) -> MatchResult:
    """Crea una partida nueva y simula `turns` turnos."""

    with transaction.atomic():
        partida = Partida.objects.create(id_partida=_new_id("PAUTO"), numero_jugadores=2)

        j_heur = Jugador.objects.create(id_jugador=_new_id("JH"), nombre="IA Heur", humano=False, numero=1)
        j_mcts = Jugador.objects.create(id_jugador=_new_id("JM"), nombre="IA MCTS", humano=False, numero=2)

        IA.objects.create(jugador=j_heur, nivel=1)
        IA.objects.create(jugador=j_mcts, nivel=2)

        JugadorPartida.objects.create(jugador=j_heur, partida=partida, orden_participacion=1)
        JugadorPartida.objects.create(jugador=j_mcts, partida=partida, orden_participacion=2)

        punta_h = _initialize_pieces_for_player(partida, j_heur, orden_participacion=1)
        punta_m = _initialize_pieces_for_player(partida, j_mcts, orden_participacion=2)

        turno = _make_turn(partida, numero=1, jugador=j_heur)

        heuristic_agent = MaxHeuristicAgent()
        mcts_agent = MCTSAgent()

        heur_stats = PlayerStats(jugador_id=j_heur.id_jugador, label=f"Heurística (punta {punta_h})")
        mcts_stats = PlayerStats(jugador_id=j_mcts.id_jugador, label=f"MCTS (punta {punta_m}, iters={iterations_mcts})")

        heur_stats.total_dist_start = _total_distance_to_goal(partida.id_partida, j_heur.id_jugador)
        mcts_stats.total_dist_start = _total_distance_to_goal(partida.id_partida, j_mcts.id_jugador)

        for t in range(1, int(turns) + 1):
            jugador = turno.jugador
            jugador_id = str(jugador.id_jugador)
            is_heur = jugador_id == str(j_heur.id_jugador)

            stats = heur_stats if is_heur else mcts_stats

            dist_before = _total_distance_to_goal(partida.id_partida, jugador_id)

            # Sugerir
            if is_heur:
                payload = heuristic_agent.suggest_move(partida_id=partida.id_partida, jugador_id=jugador_id, allow_simple=True)
            else:
                payload = mcts_agent.suggest_move(
                    partida_id=partida.id_partida,
                    jugador_id=jugador_id,
                    allow_simple=True,
                    iterations=int(iterations_mcts),
                    seed=int(seed_base + t),
                )

            pieza_id = payload.get("pieza_id")
            if not pieza_id:
                raise RuntimeError("La IA no devolvió pieza_id")

            pieza = Pieza.objects.get(id_pieza=str(pieza_id))
            if str(pieza.jugador_id) != jugador_id:
                raise RuntimeError("La IA devolvió una pieza que no es del jugador")

            steps = list(_iter_steps_from_payload(payload))
            if not steps or not all(o and d for o, d in steps):
                raise RuntimeError("La IA no devolvió origen/destino")

            # coherencia: el primer origen debe coincidir con la posición actual de la pieza
            pieza.refresh_from_db()
            if str(steps[0][0]) != str(pieza.posicion):
                raise RuntimeError(
                    f"Origen sugerido no coincide con pieza.posicion: sugerido={steps[0][0]} actual={pieza.posicion}"
                )

            # validar y aplicar
            occupied = set(get_occupied_positions(partida.id_partida))
            chain_mode = len(steps) > 1
            if chain_mode:
                stats.chains += 1
                stats.chain_steps += len(steps)

            for i, (origin, dest) in enumerate(steps, start=1):
                allow_simple_step = (not chain_mode) and i == 1
                if chain_mode:
                    allow_simple_step = False

                ok, msg = validate_move(origin, dest, occupied, allow_simple=allow_simple_step)
                if not ok:
                    stats.invalid_moves += 1
                    raise RuntimeError(f"Movimiento inválido: {msg} ({origin}->{dest})")

                Movimiento.objects.create(
                    id_movimiento=_new_id(f"M{t}_{i}"),
                    jugador=jugador,
                    pieza=pieza,
                    turno=turno,
                    partida=partida,
                    origen=origin,
                    destino=dest,
                )
                _apply_step_to_occupied(occupied, origin, dest)
                pieza.posicion = dest
                pieza.save(update_fields=["posicion"])

            stats.moves += 1

            dist_after = _total_distance_to_goal(partida.id_partida, jugador_id)
            stats.progress_sum += float(dist_before - dist_after)

            # cerrar turno actual y crear el siguiente
            turno.fin = timezone.now()
            turno.save(update_fields=["fin"])

            next_player = j_mcts if is_heur else j_heur
            turno = _make_turn(partida, numero=t + 1, jugador=next_player)

        heur_stats.total_dist_end = _total_distance_to_goal(partida.id_partida, j_heur.id_jugador)
        mcts_stats.total_dist_end = _total_distance_to_goal(partida.id_partida, j_mcts.id_jugador)
        heur_stats.in_goal_end = _pieces_in_goal(partida.id_partida, j_heur.id_jugador)
        mcts_stats.in_goal_end = _pieces_in_goal(partida.id_partida, j_mcts.id_jugador)

        jugadores_ids = [j_heur.id_jugador, j_mcts.id_jugador]
        partida.delete()
        Jugador.objects.filter(id_jugador__in=jugadores_ids).delete()

        return MatchResult(turns=turns, heuristic=heur_stats, mcts=mcts_stats)


def _print_match_analysis(result: MatchResult) -> None:
    _print_header(f"ANÁLISIS - {result.turns} turnos")

    def line(ps: PlayerStats) -> str:
        return (
            f"{ps.label}: moves={ps.moves} cadenas={ps.chains} pasosCadena={ps.chain_steps} "
            f"distStart={ps.total_dist_start:.1f} distEnd={ps.total_dist_end:.1f} "
            f"delta={ps.delta_total_dist:.1f} avgProg/move={ps.avg_progress_per_move:.3f} "
            f"enMeta(end)={ps.in_goal_end}/10"
        )

    print(line(result.heuristic))
    print(line(result.mcts))
    print(f"Mejor (por reducción de distancia total): {result.winner_by_distance()}")


def main() -> int:
    iterations_mcts = 250
    seed_base = 123

    results: List[MatchResult] = []

    for turns in (10, 30, 50, 70, 90, 110):
        res = run_match(turns=turns, iterations_mcts=iterations_mcts, seed_base=seed_base)
        results.append(res)
        _print_match_analysis(res)

    _print_header("RESUMEN GLOBAL")

    total_moves_h = sum(r.heuristic.moves for r in results)
    total_moves_m = sum(r.mcts.moves for r in results)

    delta_h = sum(r.heuristic.delta_total_dist for r in results)
    delta_m = sum(r.mcts.delta_total_dist for r in results)

    avg_prog_h = (
        sum(r.heuristic.progress_sum for r in results) / float(total_moves_h)
        if total_moves_h
        else 0.0
    )
    avg_prog_m = (
        sum(r.mcts.progress_sum for r in results) / float(total_moves_m)
        if total_moves_m
        else 0.0
    )

    wins_h = sum(1 for r in results if r.winner_by_distance() == "heuristica")
    wins_m = sum(1 for r in results if r.winner_by_distance() == "mcts")
    ties = len(results) - wins_h - wins_m

    print(f"Heurística: deltaTotalDist acumulado={delta_h:.1f}, avgProg/move={avg_prog_h:.3f}, 'victorias'={wins_h}")
    print(f"MCTS:       deltaTotalDist acumulado={delta_m:.1f}, avgProg/move={avg_prog_m:.3f}, 'victorias'={wins_m}")
    print(f"Empates:    {ties}")

    mejor_global = "heuristica" if delta_h > delta_m else "mcts" if delta_m > delta_h else "empate"
    print(f"Mejor global (por deltaTotalDist acumulado): {mejor_global}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
