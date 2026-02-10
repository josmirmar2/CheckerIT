import pytest
from rest_framework.test import APIClient


_AUTO = object()


@pytest.fixture()
def make_jugador(db):
    from game.models import Jugador

    def _make_jugador(
        *,
        id_jugador: str = "J1",
        nombre: str = "Jugador",
        humano: bool = True,
        numero: int = 1,
        **extra,
    ):
        return Jugador.objects.create(
            id_jugador=id_jugador,
            nombre=nombre,
            humano=humano,
            numero=numero,
            **extra,
        )

    return _make_jugador


@pytest.fixture()
def make_partida(db):
    from game.models import Partida

    def _make_partida(*, id_partida: str = "P1", numero_jugadores: int = 2, **extra):
        return Partida.objects.create(
            id_partida=id_partida,
            numero_jugadores=numero_jugadores,
            **extra,
        )

    return _make_partida


@pytest.fixture()
def make_turno(db, make_jugador, make_partida):
    from game.models import Turno

    def _make_turno(
        *,
        id_turno: str = "T1",
        jugador=_AUTO,
        numero: int = 1,
        partida=_AUTO,
        **extra,
    ):
        if jugador is _AUTO:
            jugador = make_jugador()
        if partida is _AUTO:
            partida = make_partida()
        return Turno.objects.create(
            id_turno=id_turno,
            jugador=jugador,
            numero=numero,
            partida=partida,
            **extra,
        )

    return _make_turno


@pytest.fixture()
def make_pieza(db, make_jugador, make_partida):
    from game.models import Pieza

    def _make_pieza(
        *,
        id_pieza: str = "X1",
        tipo: str = "punta-0",
        posicion: str = "0-0",
        jugador=_AUTO,
        partida=_AUTO,
        ia=None,
        chatbot=None,
        **extra,
    ):
        if jugador is _AUTO:
            jugador = make_jugador()
        if partida is _AUTO:
            partida = None
        return Pieza.objects.create(
            id_pieza=id_pieza,
            tipo=tipo,
            posicion=posicion,
            jugador=jugador,
            partida=partida,
            ia=ia,
            chatbot=chatbot,
            **extra,
        )

    return _make_pieza


@pytest.fixture()
def make_movimiento(db, make_jugador, make_partida, make_turno, make_pieza):
    from game.models import Movimiento

    def _make_movimiento(
        *,
        id_movimiento: str = "M1",
        jugador=_AUTO,
        partida=_AUTO,
        turno=_AUTO,
        pieza=_AUTO,
        origen: str = "0-0",
        destino: str = "0-1",
        **extra,
    ):
        if partida is _AUTO:
            partida = make_partida()
        if jugador is _AUTO:
            jugador = make_jugador()
        if pieza is _AUTO:
            pieza = make_pieza(jugador=jugador, partida=partida, posicion=origen)
        if turno is _AUTO:
            turno = make_turno(jugador=jugador, partida=partida)
        return Movimiento.objects.create(
            id_movimiento=id_movimiento,
            jugador=jugador,
            pieza=pieza,
            turno=turno,
            partida=partida,
            origen=origen,
            destino=destino,
            **extra,
        )

    return _make_movimiento


@pytest.fixture()
def make_ia(db, make_jugador):
    from game.models import IA

    def _make_ia(
        *,
        jugador=_AUTO,
        nivel: int = 1,
        **extra,
    ):
        if jugador is _AUTO:
            jugador = make_jugador(humano=False)
        return IA.objects.create(
            jugador=jugador,
            nivel=nivel,
            **extra,
        )

    return _make_ia


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()
