import pytest

from game.views import validate_move


def test_validate_move_rejects_missing_origin_or_dest():
    ok, msg = validate_move(None, "0-1", occupied_positions=set())
    assert ok is False
    assert "obligatorios" in msg


def test_validate_move_rejects_origin_equals_destination():
    ok, msg = validate_move("0-0", "0-0", occupied_positions={"0-0"})
    assert ok is False


def test_validate_move_simple_adjacent_ok():
    # En este tablero, '0-0' tiene vecino '0-1'
    ok, msg = validate_move("0-0", "0-1", occupied_positions={"0-0"}, allow_simple=True)
    assert ok is True
    assert msg == ""


def test_validate_move_simple_not_allowed_when_allow_simple_false():
    ok, msg = validate_move("0-0", "0-1", occupied_positions={"0-0"}, allow_simple=False)
    assert ok is False


def test_validate_move_jump_ok():
    # salto: 0-0 -> 0-2 si 0-1 está ocupado
    ok, msg = validate_move("0-0", "0-2", occupied_positions={"0-0", "0-1"}, allow_simple=True)
    assert ok is True
    assert msg == ""


def test_validate_move_rejects_destination_occupied():
    ok, msg = validate_move("0-0", "0-1", occupied_positions={"0-0", "0-1"}, allow_simple=True)
    assert ok is False
    assert "ocupado" in msg
