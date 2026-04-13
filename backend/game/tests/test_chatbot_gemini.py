import pytest

from rest_framework.test import APIClient


@pytest.mark.django_db
def test_chatbot_send_message_fallback_without_api_key(settings):
    settings.GEMINI_API_KEY = None

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {"mensaje": "hola"},
        format="json",
    )

    assert res.status_code == 200
    assert "respuesta" in res.data


@pytest.mark.django_db
def test_chatbot_send_message_uses_gemini_and_persists(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_MODEL = "gemini-1.5-flash"
    settings.GEMINI_TIMEOUT_SECONDS = 15
    settings.CHATBOT_DOMAIN_ENFORCE = False

    class _FakeResponse:
        status_code = 200

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "Respuesta de prueba"},
                            ]
                        }
                    }
                ]
            }

        @property
        def text(self):
            return "OK"

    def fake_post(*args, **kwargs):
        return _FakeResponse()

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {"mensaje": "¿qué puedo hacer?"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["respuesta"] == "Respuesta de prueba"
    assert res.data["chatbot_id"]

    # Segunda llamada: debe mantener chatbot_id y no fallar
    chatbot_id = res.data["chatbot_id"]
    res2 = client.post(
        "/api/chatbot/send_message/",
        {"mensaje": "segunda", "chatbot_id": chatbot_id},
        format="json",
    )
    assert res2.status_code == 200
    assert res2.data["chatbot_id"] == chatbot_id


@pytest.mark.django_db
def test_gemini_retries_on_503_then_succeeds(settings, monkeypatch):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_API_VERSION = "v1"
    settings.GEMINI_MODEL = "gemini-any"
    settings.GEMINI_MAX_RETRIES = 2
    settings.GEMINI_RETRY_BACKOFF_SECONDS = 0
    settings.CHATBOT_DOMAIN_ENFORCE = False

    calls = {"n": 0}

    class _Resp503:
        status_code = 503

        def json(self):
            return {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}}

        @property
        def text(self):
            return "503"

    class _Resp200:
        status_code = 200

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

        @property
        def text(self):
            return "OK"

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp503()
        return _Resp200()

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)
    monkeypatch.setattr("game.ai.gemini_api.time.sleep", lambda *_args, **_kwargs: None)

    client = APIClient()
    res = client.post(
        "/api/chatbot/send_message/",
        {"mensaje": "hola"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["respuesta"] == "ok"
    assert calls["n"] >= 2
