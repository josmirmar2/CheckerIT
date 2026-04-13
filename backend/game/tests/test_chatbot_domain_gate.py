import pytest

from rest_framework.test import APIClient


@pytest.mark.django_db
def test_domain_gate_rejects_offtopic_without_calling_gemini(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.CHATBOT_DOMAIN_ENFORCE = True
    settings.CHATBOT_DOMAIN_KEYWORDS = "checkerit,reglas,tablero"
    settings.CHATBOT_REFUSAL_MESSAGE = "Fuera de dominio"

    def boom(*_args, **_kwargs):
        raise AssertionError("No debería llamar a Gemini si es fuera de dominio")

    monkeypatch.setattr("game.ai.gemini_api.requests.post", boom)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {"mensaje": "dime una receta de paella"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["respuesta"] == "Fuera de dominio"


@pytest.mark.django_db
def test_domain_gate_allows_in_domain_and_calls_gemini(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_API_VERSION = "v1"
    settings.GEMINI_MODEL = "models/gemini-any"
    settings.GEMINI_MAX_RETRIES = 0
    settings.GEMINI_RETRY_BACKOFF_SECONDS = 0
    settings.CHATBOT_DOMAIN_ENFORCE = True
    settings.CHATBOT_DOMAIN_KEYWORDS = "checkerit,reglas,tablero"

    class _Resp200:
        status_code = 200

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "Respuesta"}]}}]}

        @property
        def text(self):
            return "OK"

    called = {"n": 0}

    def fake_post(*_args, **_kwargs):
        called["n"] += 1
        return _Resp200()

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {"mensaje": "¿Cuáles son las reglas del tablero?"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["respuesta"] == "Respuesta"
    assert called["n"] >= 1
