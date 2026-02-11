from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Iterable, Optional

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

from game.ai.mcts_agent import MCTSAgent   
from game.models import IA, Jugador, JugadorPartida, Movimiento, Partida, Pieza, Turno   
from game.views import get_occupied_positions, validate_move   


def _new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().timestamp()}"


def _print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _apply_step_to_occupied(occupied: set[str], origin: str, dest: str) -> None:
    occupied.discard(str(origin))
    occupied.add(str(dest))


def _iter_steps_from_payload(payload: dict) -> Iterable[tuple[str, str]]:
    secuencia = payload.get("secuencia")
    if isinstance(secuencia, list) and secuencia:
        for step in secuencia:
            yield str(step.get("origen")), str(step.get("destino"))
        return
    yield str(payload.get("origen")), str(payload.get("destino"))


def main() -> int:
    iterations = 200
    rollout_depth: Optional[int] = None
    seed: Optional[int] = 123

    with transaction.atomic():
        _print_header("MCTS (SIN REQUESTS) - SETUP")

        # 1) Crear partida y jugadores
        partida = Partida.objects.create(id_partida=_new_id("PMCTS"), numero_jugadores=2)

        j1 = Jugador.objects.create(id_jugador=_new_id("J1"), nombre="IA 1", humano=False, numero=1)
        j2 = Jugador.objects.create(id_jugador=_new_id("J2"), nombre="Humano 2", humano=True, numero=2)

        IA.objects.create(jugador=j1, nivel=2)

        JugadorPartida.objects.create(jugador=j1, partida=partida, orden_participacion=1)
        JugadorPartida.objects.create(jugador=j2, partida=partida, orden_participacion=2)

        turno = Turno.objects.create(id_turno=f"T1_{partida.id_partida}", jugador=j1, numero=1, partida=partida)

    # 2) Crear piezas en posiciones que permitan un salto
    # Nota: la validez exacta depende de la geometría del tablero ya definida.
    # Montamos un patrón típico de salto: origen -> landing con una pieza intermedia.
    # Usamos coordenadas conocidas del tablero (col-fila):
    # - P1 en 0-4, pieza intermedia en 1-4, landing en 2-4 (si existen y están alineadas)
    # Si esa línea no es válida en tu tablero, MCTS igualmente encontrará otro movimiento legal.

        pieza_inicial = Pieza.objects.create(
            id_pieza=_new_id("P1"),
            tipo="1-rojo",
            posicion="0-4",
            jugador=j1,
            partida=partida,
        )
    # pieza intermedia (puede ser propia o rival)
        Pieza.objects.create(
            id_pieza=_new_id("PX"),
            tipo="2-azul",
            posicion="1-4",
            jugador=j2,
            partida=partida,
        )
    # otra pieza del jugador (para asegurar que NO se mueve más de una)
        Pieza.objects.create(
            id_pieza=_new_id("P1B"),
            tipo="1-rojo",
            posicion="0-5",
            jugador=j1,
            partida=partida,
        )

        print(f"Partida: {partida.id_partida}")
        print(f"Turno:   {turno.id_turno} (jugador IA: {j1.id_jugador})")

        # 3) Ejecutar MCTS
        _print_header("MCTS (SIN REQUESTS) - SUGERENCIA")

        agent = MCTSAgent()
        kwargs = {
            "partida_id": partida.id_partida,
            "jugador_id": j1.id_jugador,
            "allow_simple": True,
            "iterations": int(iterations),
        }
        if rollout_depth is not None:
            kwargs["rollout_depth"] = int(rollout_depth)
        if seed is not None:
            kwargs["seed"] = int(seed)

        suggestion = agent.suggest_move(**kwargs)

        print("SUGERENCIA MCTS:")
        print(suggestion)

        pieza_id = suggestion.get("pieza_id")
        assert pieza_id, "La sugerencia no incluye pieza_id"

        # 4) Validaciones de coherencia (pieza/turno)
        pieza = Pieza.objects.get(id_pieza=pieza_id)
        assert str(pieza.jugador_id) == str(j1.id_jugador), "MCTS devolvió una pieza que no es del jugador"
        assert str(pieza.partida_id) == str(partida.id_partida), "MCTS devolvió una pieza que no es de la partida"
        assert turno.fin is None, "El turno ya está finalizado"

        steps = list(_iter_steps_from_payload(suggestion))
        assert steps and all(o and d for o, d in steps), "La sugerencia no incluye origen/destino válidos"

        # el origen del primer paso debe coincidir con la posición real
        pieza.refresh_from_db()
        expected_origin = str(pieza.posicion)
        assert str(steps[0][0]) == expected_origin, (
            f"El origen de la sugerencia no coincide con la posición actual de la pieza: "
            f"recibido={steps[0][0]} esperado={expected_origin}"
        )

        # 5) Validar legalidad (validate_move) paso a paso
        _print_header("MCTS (SIN REQUESTS) - VALIDACIÓN")

        occupied = set(get_occupied_positions(partida.id_partida))
        chain_mode = len(steps) > 1

        for i, (origin, dest) in enumerate(steps, start=1):
            allow_simple_step = (not chain_mode) and i == 1
            if chain_mode:
                allow_simple_step = False
            ok, msg = validate_move(origin, dest, occupied, allow_simple=allow_simple_step)
            assert ok, f"Paso inválido según validate_move: {msg} ({origin}->{dest})"
            _apply_step_to_occupied(occupied, origin, dest)

        print("OK: validate_move acepta la jugada sugerida.")

        # 6) Persistir en BD (un movimiento por paso) + actualizar pieza
        _print_header("MCTS (SIN REQUESTS) - PERSISTENCIA")

        for i, (origin, dest) in enumerate(steps, start=1):
            Movimiento.objects.create(
                id_movimiento=_new_id(f"M{i}"),
                jugador=j1,
                pieza=pieza,
                turno=turno,
                partida=partida,
                origen=origin,
                destino=dest,
            )
            pieza.posicion = dest
            pieza.save(update_fields=["posicion"])

        pieza.refresh_from_db()
        assert str(pieza.posicion) == str(steps[-1][1]), "La posición final de la pieza no coincide con el último destino"

        print("OK: movimientos creados en BD y pieza actualizada correctamente.")

        _print_header("MCTS (SIN REQUESTS) - RESULTADO")
        print("OK: MCTS sugiere una jugada legal y de una sola pieza (incluyendo cadenas si aplica).")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
