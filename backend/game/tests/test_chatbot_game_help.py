import pytest

from rest_framework.test import APIClient

from game.models import Jugador, Partida, Pieza, JugadorPartida, Ronda


def _new_id(prefix: str) -> str:
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

    Ronda.objects.create(id_ronda=_new_id("R"), jugador=j1, numero=1, partida=partida)

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
    assert res.data["sugerencia"].get("heuristica") == "mcts"

    chatbot_id = res.data.get("chatbot_id")
    assert chatbot_id

    res2 = client.post(
        "/api/chatbot/send_message/",
        {
            "mensaje": "muéstramelo",
            "chatbot_id": chatbot_id,
        },
        format="json",
    )
    assert res2.status_code == 200
    assert res2.data.get("tipo") == "mostrar_movimiento"
    assert isinstance(res2.data.get("sugerencia"), dict)


@pytest.mark.django_db
def test_chatbot_possible_moves_returns_local_moves_without_gemini(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.CHATBOT_DOMAIN_ENFORCE = True

    def boom(*_args, **_kwargs):
        raise AssertionError("No debería llamar a Gemini en movimientos posibles")

    monkeypatch.setattr("game.ai.gemini_api.requests.post", boom)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {
            "mensaje": "Quiero ver los movimientos posibles",
        },
        format="json",
    )

    assert res.status_code == 200
    assert res.data.get("tipo") == "movimientos_no_disponible"
