import pytest

from game.views import validate_move


def test_validar_movimiento_rechaza_origen_o_destino_faltante():
    ok, msg = validate_move(None, "0-1", occupied_positions=set())
    assert ok is False
    assert "obligatorios" in msg


def test_validar_movimiento_rechaza_origen_igual_destino():
    ok, msg = validate_move("0-0", "0-0", occupied_positions={"0-0"})
    assert ok is False


def test_validar_movimiento_simple_adyacente_ok():
    # En este tablero, '0-0' tiene vecino '0-1'
    ok, msg = validate_move("0-0", "0-1", occupied_positions={"0-0"}, allow_simple=True)
    assert ok is True
    assert msg == ""


def test_validar_movimiento_simple_no_permitido_si_allow_simple_false():
    ok, msg = validate_move("0-0", "0-1", occupied_positions={"0-0"}, allow_simple=False)
    assert ok is False


def test_validar_movimiento_salto_ok():
    # salto: 0-0 -> 0-2 si 0-1 está ocupado
    ok, msg = validate_move("0-0", "0-2", occupied_positions={"0-0", "0-1"}, allow_simple=True)
    assert ok is True
    assert msg == ""


def test_validar_movimiento_rechaza_destino_ocupado():
    ok, msg = validate_move("0-0", "0-1", occupied_positions={"0-0", "0-1"}, allow_simple=True)
    assert ok is False
    assert "ocupado" in msg