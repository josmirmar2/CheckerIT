import pytest

from rest_framework.test import APIClient

from game.models import Jugador, Partida, Pieza, JugadorPartida


def _new_id(prefix: str) -> str:
    # Suficientemente único para tests sin depender de tiempo exacto
    import uuid

    return f"{prefix}_{uuid.uuid4().hex}"[:50]


@pytest.mark.django_db
def test_chatbot_best_move_returns_local_suggestion_without_gemini(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.CHATBOT_DOMAIN_ENFORCE = True

    def boom(*_args, **_kwargs):
        raise AssertionError("No debería llamar a Gemini en mejor jugada")

    monkeypatch.setattr("game.ai.gemini_api.requests.post", boom)

    partida = Partida.objects.create(id_partida=_new_id("P"), numero_jugadores=2)
    j1 = Jugador.objects.create(id_jugador=_new_id("J1"), nombre="J1", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador=_new_id("J2"), nombre="J2", humano=True, numero=2)

    JugadorPartida.objects.create(jugador=j1, partida=partida, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=partida, orden_participacion=2)

    # Piezas mínimas para que exista al menos un movimiento legal
    Pieza.objects.create(id_pieza=_new_id("PZ1"), tipo="1-rojo", posicion="0-4", jugador=j1, partida=partida)
    Pieza.objects.create(id_pieza=_new_id("PZ2"), tipo="2-azul", posicion="1-4", jugador=j2, partida=partida)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {
            "mensaje": "¿Cuál es la mejor jugada?",
            "partida_id": partida.id_partida,
            "jugador_id": j1.id_jugador,
        },
        format="json",
    )

    assert res.status_code == 200
    assert "respuesta" in res.data
    assert res.data.get("tipo") == "mejor_jugada"
    assert isinstance(res.data.get("sugerencia"), dict)


@pytest.mark.django_db
def test_chatbot_possible_moves_returns_local_moves_without_gemini(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.CHATBOT_DOMAIN_ENFORCE = True

    def boom(*_args, **_kwargs):
        raise AssertionError("No debería llamar a Gemini en movimientos posibles")

    monkeypatch.setattr("game.ai.gemini_api.requests.post", boom)

    partida = Partida.objects.create(id_partida=_new_id("P"), numero_jugadores=2)
    j1 = Jugador.objects.create(id_jugador=_new_id("J1"), nombre="J1", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador=_new_id("J2"), nombre="J2", humano=True, numero=2)

    JugadorPartida.objects.create(jugador=j1, partida=partida, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=partida, orden_participacion=2)

    pz1 = Pieza.objects.create(id_pieza=_new_id("PZ1"), tipo="1-rojo", posicion="0-4", jugador=j1, partida=partida)
    Pieza.objects.create(id_pieza=_new_id("PZ2"), tipo="2-azul", posicion="1-4", jugador=j2, partida=partida)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {
            "mensaje": "Quiero ver los movimientos posibles",
            "partida_id": partida.id_partida,
            "jugador_id": j1.id_jugador,
            "pieza_id": pz1.id_pieza,
        },
        format="json",
    )

    assert res.status_code == 200
    assert res.data.get("tipo") == "movimientos"
    movimientos = res.data.get("movimientos")
    assert isinstance(movimientos, dict)
    assert str(pz1.id_pieza) in movimientos or movimientos == {}
