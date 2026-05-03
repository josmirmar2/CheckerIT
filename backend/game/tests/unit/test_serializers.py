import pytest

from django.core.exceptions import ValidationError
from rest_framework import serializers

from game.models import (
    is_valid_position_key, validate_position_key,
    Jugador, Partida, Pieza, Ronda, Movimiento, JugadorPartida
)
from game.serializers import PiezaSerializer, MovimientoSerializer, JugadorPartidaSerializer


def test_is_valid_position_key_basic():
    assert is_valid_position_key('0-0')
    assert not is_valid_position_key('foo')
    assert not is_valid_position_key('100-100')
    assert not is_valid_position_key(123)


def test_validate_position_key_raises():
    with pytest.raises(ValidationError):
        validate_position_key('bad')


@pytest.mark.django_db
def test_pieza_serializer_validate_posicion():
    jugador = Jugador.objects.create(id_jugador='J1', nombre='J1', humano=True)
    partida = Partida.objects.create(id_partida='P1', numero_jugadores=2)

    data = {'id_pieza': 'PZ1', 'tipo': 'ficha', 'posicion': 'invalid', 'jugador': jugador.id_jugador, 'partida': partida.id_partida}
    s = PiezaSerializer(data=data)
    assert not s.is_valid()
    assert 'posicion' in s.errors


@pytest.mark.django_db
def test_movimiento_serializer_origen_must_match_pieza():
    p = Partida.objects.create(id_partida='P3', numero_jugadores=2)
    j = Jugador.objects.create(id_jugador='J2', nombre='J2', humano=True)
    pieza = Pieza.objects.create(id_pieza='PX', tipo='f', posicion='0-0', jugador=j, partida=p)
    # Crear una ronda válida para pasar la validación previa
    from game.models import Ronda as RModel
    ronda = RModel.objects.create(id_ronda='RR1', jugador=j, numero=1, partida=p)

    data = {'id_movimiento': 'MV1', 'jugador': j.id_jugador, 'pieza': pieza.id_pieza, 'ronda': ronda.id_ronda, 'partida': p.id_partida, 'origen': '1-1', 'destino': '2-2'}
    s = MovimientoSerializer(data=data)
    assert not s.is_valid()
    assert 'origen' in s.errors or 'non_field_errors' in s.errors


@pytest.mark.django_db
def test_jugadorpartida_serializer_limits_and_duplicates():
    p = Partida.objects.create(id_partida='PX', numero_jugadores=2)
    j1 = Jugador.objects.create(id_jugador='A', nombre='A', humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador='B', nombre='B', humano=True, numero=2)
    j3 = Jugador.objects.create(id_jugador='C', nombre='C', humano=True, numero=3)

    # fill limit
    JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

    s = JugadorPartidaSerializer(data={'jugador': j3.id_jugador, 'partida': p.id_partida, 'orden_participacion': 3})
    assert not s.is_valid()
    assert 'partida' in s.errors or 'orden_participacion' in s.errors
