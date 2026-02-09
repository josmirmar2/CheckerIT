import pytest
from django.db import IntegrityError

from game.models import Jugador, Partida, JugadorPartida


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
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

    JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

    with pytest.raises(IntegrityError):
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=2)


@pytest.mark.django_db
def test_pieza_str():
    p = Partida.objects.create(id_pieza="Piece1", numero_jugadores=2)
    assert str(p) == "Partida P1"