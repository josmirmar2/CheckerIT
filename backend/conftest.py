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


@pytest.fixture(autouse=True)
def _disable_gemini_in_tests(settings):
    """Evita llamadas externas a Gemini en tests.

    Los tests que quieran cubrir la integración con Gemini deben establecer
    `settings.GEMINI_API_KEY` y mockear `requests` explícitamente.
    """
    settings.GEMINI_API_KEY = None


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
def make_ronda(db, make_jugador, make_partida):
    from game.models import Ronda

    def _make_ronda(
        *,
        id_ronda: str = "R1",
        jugador=_AUTO,
        numero: int = 1,
        partida=_AUTO,
        **extra,
    ):
        if jugador is _AUTO:
            jugador = make_jugador()
        if partida is _AUTO:
            partida = make_partida()
        return Ronda.objects.create(
            id_ronda=id_ronda,
            jugador=jugador,
            numero=numero,
            partida=partida,
            **extra,
        )

    return _make_ronda


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
            chatbot=chatbot,
            **extra,
        )

    return _make_pieza


@pytest.fixture()
def make_movimiento(db, make_jugador, make_partida, make_ronda, make_pieza):
    from game.models import Movimiento

    def _make_movimiento(
        *,
        id_movimiento: str = "M1",
        jugador=_AUTO,
        partida=_AUTO,
        ronda=_AUTO,
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
        if ronda is _AUTO:
            ronda = make_ronda(jugador=jugador, partida=partida)
        return Movimiento.objects.create(
            id_movimiento=id_movimiento,
            jugador=jugador,
            pieza=pieza,
            ronda=ronda,
            partida=partida,
            origen=origen,
            destino=destino,
            **extra,
        )

    return _make_movimiento


@pytest.fixture()
def make_agente_inteligente(db, make_jugador):
    from game.models import AgenteInteligente

    def _make_agente_inteligente(
        *,
        jugador=_AUTO,
        nivel: int = 1,
        **extra,
    ):
        if jugador is _AUTO:
            jugador = make_jugador(humano=False)
        return AgenteInteligente.objects.create(
            jugador=jugador,
            nivel=nivel,
            **extra,
        )

    return _make_agente_inteligente


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()
