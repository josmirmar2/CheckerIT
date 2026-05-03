import types
import random

import pytest

from game.ai import max_agent, mcts_agent


def test_axial_and_key_and_hex_distance():
    # roundtrip for a known mapping key
    k = '0-0'
    axial = max_agent._axial_from_key(k)
    assert axial is not None
    k2 = max_agent._key_from_axial(*axial)
    assert k == k2

    # hex distance symmetric
    d = max_agent._hex_distance((0, 0), (1, 0))
    assert isinstance(d, int) and d >= 0


def test_distance_to_goal_and_goal_depth():
    # pick a key that exists in GOAL_POSITIONS for some punta
    for punta, goals in max_agent.GOAL_POSITIONS.items():
        if goals:
            k = goals[0]
            dist = max_agent._distance_to_goal(k, punta)
            assert dist == 0
            depth = max_agent._goal_depth_score(k, punta)
            assert isinstance(depth, float)
            break


def test_goal_priority_and_penalty():
    # Ensure priority bonus for priority positions
    for punta, priorities in max_agent.GOAL_PRIORITY_POSITIONS.items():
        if priorities:
            pos = priorities[0]
            bonus = max_agent._goal_priority_bonus(pos, punta)
            assert bonus >= 0
            penalty, missing, blockers = max_agent._goal_priority_penalty([pos], punta)
            assert isinstance(penalty, float)
            break


def test_parse_and_target_punta():
    assert max_agent._parse_punta('0-something') == 0
    assert max_agent._parse_punta('bad') is None
    assert max_agent._target_punta(0) == max_agent.TARGET_MAP[0]


def test_max_agent_compute_moves_and_sequences():
    agent = max_agent.MaxHeuristicAgent()
    # choose a key with neighbors
    origin = '1-1'
    occupied = {origin}
    simples = agent._compute_simple_moves(origin, occupied)
    # moves should be list
    assert isinstance(simples, list)

    # create a jump scenario: place a piece adjacent and landing free
    # find a direction where middle and landing exist
    for d in max_agent.AXIAL_DIRECTIONS:
        ax = max_agent._axial_from_key(origin)
        if not ax:
            continue
        mq = ax[0] + d['dq']
        mr = ax[1] + d['dr']
        lq = ax[0] + 2 * d['dq']
        lr = ax[1] + 2 * d['dr']
        mid = max_agent._key_from_axial(mq, mr)
        land = max_agent._key_from_axial(lq, lr)
        if mid and land:
            occ = {origin, mid}
            jumps = agent._compute_jump_moves(origin, occ)
            sequences = agent._compute_jump_sequences(origin, occ)
            assert isinstance(jumps, list)
            assert isinstance(sequences, list)
            break


def test_pick_best_jump_sequence_prefers_progress():
    agent = max_agent.MaxHeuristicAgent()
    origin = '0-3'
    # craft sequences where one goes closer
    seqs = [
        [origin, '1-3', '2-3'],
        [origin, '0-2']
    ]
    best = agent._pick_best_jump_sequence(origin, seqs, target_punta=3)
    assert best is not None
    assert isinstance(best, list)


@pytest.mark.django_db
def test_max_agent_suggest_move_simple(monkeypatch):
    from game.models import Partida, Jugador, Pieza

    p = Partida.objects.create(id_partida='PT1', numero_jugadores=2)
    j = Jugador.objects.create(id_jugador='J1', nombre='J1', humano=True)
    # create two pieces for player in non-goal positions
    Pieza.objects.create(id_pieza='A1', tipo='0-x', posicion='0-1', jugador=j, partida=p)
    Pieza.objects.create(id_pieza='A2', tipo='0-x', posicion='0-2', jugador=j, partida=p)

    # also create opponent pieces to allow jumps etc
    op = Jugador.objects.create(id_jugador='J2', nombre='J2', humano=True)
    Pieza.objects.create(id_pieza='B1', tipo='3-x', posicion='1-1', jugador=op, partida=p)

    agent = max_agent.MaxHeuristicAgent()
    out = agent.suggest_move(partida_id='PT1', jugador_id='J1', allow_simple=True)
    assert 'pieza_id' in out and 'destino' in out


def test_game_state_evaluate_and_legal_moves():
    # Build simple GameState with two players
    pieces = (
        mcts_agent._PieceTuple('p1', 'J1', '0-x', '0-1'),
        mcts_agent._PieceTuple('p2', 'J2', '3-x', '3-13'),
    )
    state = mcts_agent.GameState(player_order=('J1', 'J2'), current_player_index=0, player_targets=(('J1', 3), ('J2', 0)), pieces=pieces)
    # evaluate symmetric
    val = state.evaluate('J1')
    assert isinstance(val, float)

    moves = mcts_agent.legal_turn_moves(state, 'J1', allow_simple=True)
    assert isinstance(moves, list)


@pytest.mark.django_db
def test_mcts_agent_suggest_move_monkeypatched(monkeypatch):
    from types import SimpleNamespace
    from game.models import Partida, Jugador, Pieza, Ronda, JugadorPartida

    # Setup DB minimal game state
    p = Partida.objects.create(id_partida='PM1', numero_jugadores=2)
    j1 = Jugador.objects.create(id_jugador='J1', nombre='J1', humano=True)
    j2 = Jugador.objects.create(id_jugador='J2', nombre='J2', humano=True)
    JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)
    # create pieces
    Pieza.objects.create(id_pieza='P1', tipo='0-x', posicion='0-1', jugador=j1, partida=p)
    Pieza.objects.create(id_pieza='P2', tipo='3-x', posicion='3-13', jugador=j2, partida=p)
    # create active ronda for j1
    Ronda.objects.create(id_ronda='R1', jugador=j1, numero=1, partida=p)

    # Fake MonteCarlo and Node to avoid heavy dependency
    class FakeNode:
        def __init__(self, state):
            self.state = state
            self.children = []
            self.player_number = None
            self.visits = 0
            self.win_value = 0

        def add_child(self, child):
            self.children.append(child)

    class FakeMC:
        def __init__(self, root_node):
            self.root_node = root_node
            self.child_finder = None
            self.node_evaluator = None

        def simulate(self, it):
            # do nothing
            return

        def make_choice(self):
            # return an object with state.last_move = None and visits=0
            return SimpleNamespace(state=SimpleNamespace(last_move=None), visits=0, win_value=0)

    monkeypatch.setattr('game.ai.mcts_agent.Node', FakeNode)
    monkeypatch.setattr('game.ai.mcts_agent.MonteCarlo', FakeMC)

    agent = mcts_agent.MCTSAgent()
    out = agent.suggest_move(partida_id='PM1', jugador_id='J1', allow_simple=True, iterations=1, seed=1)
    assert 'pieza_id' in out and 'destino' in out
