import pytest

from game.models import Jugador, Partida, Pieza, Turno


@pytest.mark.django_db
def test_api_root_ok(api_client):
    res = api_client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data.get("mensaje")
    assert "api" in data.get("endpoints", {})


@pytest.mark.django_db
def test_start_game_creates_partida_and_turno(api_client):
    payload = {
        "numero_jugadores": 2,
        "jugadores": [
            {"tipo": "humano", "nombre": "Jugador 1", "dificultad": "Fácil", "numero": 1},
            {"tipo": "ia", "dificultad": "Difícil", "numero": 2},
        ],
    }

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    assert res.status_code == 201

    data = res.json()
    assert data["id_partida"]
    assert data["numero_jugadores"] == 2
    assert len(data["participantes"]) == 2
    assert len(data["turnos"]) == 1


@pytest.mark.django_db
def test_start_game_rejects_less_than_two_players(api_client):
    payload = {
        "numero_jugadores": 1,
        "jugadores": [
            {"tipo": "humano", "nombre": "Solo", "numero": 1},
        ],
    }

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_rejects_more_than_six_players(api_client):
    payload = {
        "numero_jugadores": 7,
        "jugadores": [
            {"tipo": "humano", "nombre": f"J{i}", "numero": i} for i in range(1, 8)
        ],
    }

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_rejects_duplicate_player_numbers(api_client):
    payload = {
        "numero_jugadores": 2,
        "jugadores": [
            {"tipo": "humano", "nombre": "A", "numero": 1},
            {"tipo": "humano", "nombre": "B", "numero": 1},
        ],
    }

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_create_pieza_rejects_invalid_position(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    payload = {
        "id_pieza": "PX1",
        "tipo": "punta-0",
        "posicion": "99-99",
        "jugador": jugador.id_jugador,
        "ia": None,
        "chatbot": None,
        "partida": None,
    }

    res = api_client.post("/api/piezas/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_create_movimiento_rejects_invalid_origen_or_destino(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    partida = Partida.objects.create(id_partida="P_API", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="PX1",
        tipo="punta-0",
        posicion="0-0",
        jugador=jugador,
        partida=partida,
    )
    turno = Turno.objects.create(id_turno="T_API", jugador=jugador, numero=1, partida=partida)

    payload_bad_origen = {
        "id_movimiento": "M_API_1",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida.id_partida,
        "origen": "99-99",
        "destino": "0-1",
    }
    res1 = api_client.post("/api/movimientos/", payload_bad_origen, format="json")
    assert res1.status_code == 400

    payload_bad_destino = {
        "id_movimiento": "M_API_2",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida.id_partida,
        "origen": "0-0",
        "destino": "99-99",
    }
    res2 = api_client.post("/api/movimientos/", payload_bad_destino, format="json")
    assert res2.status_code == 400
