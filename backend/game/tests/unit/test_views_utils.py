import pytest

from game import views


def find_adjacent_pair():
    for origin_key, coord in views.POSITION_TO_CARTESIAN.items():
        q = coord.get("q")
        r = coord.get("r")
        for d in views.AXIAL_DIRECTIONS:
            nq = q + d["dq"]
            nr = r + d["dr"]
            neighbor = views.key_from_coord(nq, nr)
            if neighbor:
                return origin_key, neighbor
    return None, None


def find_jump_triplet():
    for origin_key, coord in views.POSITION_TO_CARTESIAN.items():
        q = coord.get("q")
        r = coord.get("r")
        for d in views.AXIAL_DIRECTIONS:
            mq = q + d["dq"]
            mr = r + d["dr"]
            lq = q + 2 * d["dq"]
            lr = r + 2 * d["dr"]
            middle = views.key_from_coord(mq, mr)
            landing = views.key_from_coord(lq, lr)
            if middle and landing:
                return origin_key, middle, landing
    return None, None, None


def test_coord_roundtrip():
    for k, coord in list(views.POSITION_TO_CARTESIAN.items())[:10]:
        kk = views.key_from_coord(coord["q"], coord["r"])
        assert kk == k


def test_compute_simple_moves_neighbor_presence():
    origin, neighbor = find_adjacent_pair()
    assert origin and neighbor

    moves = views.compute_simple_moves(origin, occupied_positions=set())
    assert isinstance(moves, list)
    assert neighbor in moves


def test_compute_simple_moves_excludes_occupied():
    origin, neighbor = find_adjacent_pair()
    assert origin and neighbor

    moves = views.compute_simple_moves(origin, occupied_positions={neighbor})
    assert neighbor not in moves


def test_compute_jump_moves_basic():
    origin, middle, landing = find_jump_triplet()
    assert origin and middle and landing

    occ = {middle, origin}
    jumps = views.compute_jump_moves(origin, occupied_positions=occ)
    assert landing in jumps


def test__jump_neighbors_matches_compute_jump_moves():
    origin, middle, landing = find_jump_triplet()
    assert origin and middle and landing

    base = {p for p in [origin, middle] if p != origin}
    base_all = {middle}
    neigh = views._jump_neighbors(origin, base_all)
    assert landing in neigh


def test_find_jump_chain_path_single_jump():
    origin, middle, landing = find_jump_triplet()
    assert origin and middle and landing

    occ = {origin, middle}
    path = views.find_jump_chain_path(origin, landing, occupied_positions=occ)
    assert path is not None
    assert path[0] == origin and path[-1] == landing


def test_find_jump_chain_path_none_for_invalid():
    keys = list(views.POSITION_TO_CARTESIAN.keys())
    a = keys[0]
    b = keys[-1]
    occ = set()
    path = views.find_jump_chain_path(a, b, occupied_positions=occ)
    assert path is None


def test_validate_move_simple_and_jump():
    origin, neighbor = find_adjacent_pair()
    origin2, middle, landing = find_jump_triplet()
    assert origin and neighbor and origin2 and middle and landing

    occ = set()
    occ_simple = {origin}
    ok, msg = views.validate_move(origin, neighbor, occupied_positions=occ_simple, allow_simple=True)
    assert ok

    occ_jump = {origin2, middle}
    ok2, msg2 = views.validate_move(origin2, landing, occupied_positions=occ_jump, allow_simple=True)
    assert ok2


def test_get_valid_moves_from_includes_simple_and_jumps():
    origin, neighbor = find_adjacent_pair()
    origin2, middle, landing = find_jump_triplet()
    assert origin and neighbor and origin2 and middle and landing

    occ = {origin2, middle}
    moves = views.get_valid_moves_from(origin2, occupied_positions=occ, allow_simple=True)
    assert landing in moves


def test_validate_move_messages_and_cases():
    ok, msg = views.validate_move(None, "0-1", occupied_positions=set())
    assert ok is False
    assert "obligatorios" in msg

    ok, msg = views.validate_move("0-0", "0-0", occupied_positions={"0-0"})
    assert ok is False

    ok, msg = views.validate_move("0-0", "0-1", occupied_positions={"0-0"}, allow_simple=True)
    assert ok is True
    assert msg == ""

    ok, msg = views.validate_move("0-0", "0-1", occupied_positions={"0-0"}, allow_simple=False)
    assert ok is False

    ok, msg = views.validate_move("0-0", "0-2", occupied_positions={"0-0", "0-1"}, allow_simple=True)
    assert ok is True
    assert msg == ""

    ok, msg = views.validate_move("0-0", "0-1", occupied_positions={"0-0", "0-1"}, allow_simple=True)
    assert ok is False
    assert "ocupado" in msg
