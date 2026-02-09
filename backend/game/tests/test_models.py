import pytest
from django.db import IntegrityError, transaction

from game.models import Jugador, Partida, JugadorPartida, Pieza


@pytest.mark.django_db
def test_jugador_str():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    assert str(j) == "Ana"


@pytest.mark.django_db
def test_partida_str():
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    assert str(p) == "Partida P1"


@pytest.mark.django_db
def test_jugador_partida_unique_together():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

    JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

    with pytest.raises(IntegrityError):
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=2)


@pytest.mark.django_db
def test_jugador_partida():
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

    JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

    assert JugadorPartida.objects.filter(partida=p).count() == 2


@pytest.mark.django_db
def test_partida_numero_jugadores_between_2_and_6_enforced_by_db():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Partida.objects.create(id_partida="P_BAD_1", numero_jugadores=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Partida.objects.create(id_partida="P_BAD_7", numero_jugadores=7)

@pytest.mark.django_db
def test_pieza_str():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    partida = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=partida,
    )
    assert "punta-0" in str(pieza)
    assert "Ana" in str(pieza)