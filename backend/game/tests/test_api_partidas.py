import pytest


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
