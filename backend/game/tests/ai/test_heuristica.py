"""Prueba local (sin requests) de la IA heurística (MaxHeuristicAgent).

- No usa HTTP.
- Usa Django ORM contra la BD configurada (por defecto sqlite).
- Crea una partida mínima de 2 jugadores con un turno activo y piezas.
- Ejecuta MaxHeuristicAgent.suggest_move y valida que la jugada es legal según validate_move.
- Si devuelve una cadena (secuencia), valida cada salto como cadena (sin simples).

Ejecución (desde la raíz del repo):
    C:/Users/JoséManuel/Documents/TFG/CheckerIT/.venv/Scripts/python.exe backend/game/tests/ai/verificar_heuristica_sin_requests.py

Notas:
- Este script NO intenta medir “calidad” de la IA; comprueba legalidad y consistencia.
- Para fuerza, conviene comparar métricas (progreso, oscilación, etc.) en simulaciones.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Iterable

CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = next((p for p in CURRENT_FILE.parents if (p / "manage.py").exists()), None)
if BACKEND_DIR is None:
    raise RuntimeError("No se pudo localizar el directorio 'backend' (manage.py) para inicializar sys.path")
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "checkerit.settings")

import django    

django.setup()    

from django.utils import timezone    

from game.ai.max_agent import MaxHeuristicAgent    
from game.models import IA, Jugador, JugadorPartida, Movimiento, Partida, Pieza, Turno    
from game.views import get_occupied_positions, validate_move    


def _new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().timestamp()}"


def _apply_step_to_occupied(occupied: set[str], origin: str, dest: str) -> None:
    occupied.discard(str(origin))
    occupied.add(str(dest))


def _print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _iter_steps_from_payload(payload: dict) -> Iterable[tuple[str, str]]:
    secuencia = payload.get("secuencia")
    if isinstance(secuencia, list) and secuencia:
        for step in secuencia:
            yield str(step.get("origen")), str(step.get("destino"))
        return
    yield str(payload.get("origen")), str(payload.get("destino"))


def main() -> int:
    _print_header("HEURÍSTICA (SIN REQUESTS) - SETUP")

    # 1) Crear partida y jugadores
    partida = Partida.objects.create(id_partida=_new_id("PHEUR"), numero_jugadores=2)

    j1 = Jugador.objects.create(id_jugador=_new_id("JIA"), nombre="IA 1", humano=False, numero=1)
    j2 = Jugador.objects.create(id_jugador=_new_id("JH"), nombre="Humano 2", humano=True, numero=2)

    IA.objects.create(jugador=j1, nivel=1) 

    JugadorPartida.objects.create(jugador=j1, partida=partida, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=partida, orden_participacion=2)

    turno = Turno.objects.create(id_turno=f"T1_{partida.id_partida}", jugador=j1, numero=1, partida=partida)

    # 2) Crear piezas. Usamos coordenadas conocidas (aparecen en posiciones iniciales del backend).
    #    La heurística elegirá una jugada legal; no forzamos que sea salto.
    p1 = Pieza.objects.create(
        id_pieza=_new_id("P1"),
        tipo="1-rojo",
        posicion="0-4",
        jugador=j1,
        partida=partida,
    )
    Pieza.objects.create(
        id_pieza=_new_id("P2"),
        tipo="1-rojo",
        posicion="0-5",
        jugador=j1,
        partida=partida,
    )
    # pieza “bloque” / intermedia (puede habilitar saltos)
    Pieza.objects.create(
        id_pieza=_new_id("PX"),
        tipo="2-azul",
        posicion="1-4",
        jugador=j2,
        partida=partida,
    )

    print(f"Partida: {partida.id_partida}")
    print(f"Turno:   {turno.id_turno} (jugador IA: {j1.id_jugador})")

    _print_header("HEURÍSTICA (SIN REQUESTS) - SUGERENCIA")

    agent = MaxHeuristicAgent()
    suggestion = agent.suggest_move(partida_id=partida.id_partida, jugador_id=j1.id_jugador, allow_simple=True)

    print("SUGERENCIA MAX:")
    print(suggestion)

    pieza_id = suggestion.get("pieza_id")
    assert pieza_id, "La sugerencia no incluye pieza_id"

    pieza = Pieza.objects.get(id_pieza=pieza_id)
    assert str(pieza.jugador_id) == str(j1.id_jugador), "La heurística devolvió una pieza que no es del jugador"

    # 3) Validación paso a paso con la misma función del backend
    _print_header("HEURÍSTICA (SIN REQUESTS) - VALIDACIÓN")

    occupied = set(get_occupied_positions(partida.id_partida))

    steps = list(_iter_steps_from_payload(suggestion))
    assert all(o and d for o, d in steps), "La sugerencia no incluye origen/destino válidos"

    chain_mode = len(steps) > 1

    # La primera pieza de la cadena debe arrancar en la posición actual real
    expected_origin = str(pieza.posicion)
    assert str(steps[0][0]) == expected_origin, (
        f"El origen de la sugerencia no coincide con la posición actual de la pieza: "
        f"recibido={steps[0][0]} esperado={expected_origin}"
    )

    for i, (origin, dest) in enumerate(steps, start=1):
        allow_simple = (not chain_mode) and i == 1
        if chain_mode:
            allow_simple = False

        ok, msg = validate_move(origin, dest, occupied, allow_simple=allow_simple)
        assert ok, f"Paso inválido según validate_move: {msg} ({origin}->{dest})"
        _apply_step_to_occupied(occupied, origin, dest)

    print("OK: validate_move acepta la jugada sugerida.")

    # 4) (Opcional) Persistir movimientos en BD + actualizar pieza para mantener coherencia
    _print_header("HEURÍSTICA (SIN REQUESTS) - PERSISTENCIA")

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

    _print_header("HEURÍSTICA (SIN REQUESTS) - RESULTADO")
    print("OK: la heurística devuelve una jugada legal y consistente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
