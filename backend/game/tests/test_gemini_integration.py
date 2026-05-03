import pytest
import requests

from game.ai import gemini_api


def _make_resp(status_code=200, json_data=None, text="OK", json_exc: Exception | None = None):
    class _R:
        def __init__(self):
            self.status_code = status_code

        def json(self):
            if json_exc:
                raise json_exc
            return json_data

        @property
        def text(self):
            return text

    return _R()


def test_generate_gemini_reply_network_error_raises(monkeypatch):
    def fake_post(*_a, **_k):
        raise requests.exceptions.ConnectionError("conn fail")

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    with pytest.raises(gemini_api.GeminiError) as exc:
        gemini_api.generate_gemini_reply(api_key="key", user_message="hola")

    assert "Error de red" in str(exc.value)


def test_generate_gemini_reply_http_retryable_then_raise(monkeypatch):
    # always return 429 -> should raise GeminiHttpError after retries
    resp = _make_resp(status_code=429, json_data={"error": {"code": 429}})

    def fake_post(*_a, **_k):
        return resp

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    with pytest.raises(gemini_api.GeminiHttpError) as exc:
        gemini_api.generate_gemini_reply(
            api_key="k",
            user_message="hola",
            max_retries=0,
            retry_backoff_seconds=0,
        )

    assert exc.value.status_code == 429


def test_generate_gemini_reply_invalid_json(monkeypatch):
    resp = _make_resp(status_code=200, json_exc=ValueError("bad json"))

    def fake_post(*_a, **_k):
        return resp

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    with pytest.raises(gemini_api.GeminiError) as exc:
        gemini_api.generate_gemini_reply(api_key="k", user_message="hola")

    assert "Respuesta JSON inválida" in str(exc.value)


def test_generate_gemini_reply_no_candidates(monkeypatch):
    resp = _make_resp(status_code=200, json_data={})

    def fake_post(*_a, **_k):
        return resp

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    with pytest.raises(gemini_api.GeminiError) as exc:
        gemini_api.generate_gemini_reply(api_key="k", user_message="hola")

    assert "no devolvió candidatos" in str(exc.value).lower()


def test_generate_gemini_reply_empty_candidate_text(monkeypatch):
    data = {"candidates": [{"content": {"parts": [{"text": ""}]}}]}
    resp = _make_resp(status_code=200, json_data=data)

    def fake_post(*_a, **_k):
        return resp

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    with pytest.raises(gemini_api.GeminiError) as exc:
        gemini_api.generate_gemini_reply(api_key="k", user_message="hola")

    assert "respuesta vacía" in str(exc.value).lower()


def test_generate_gemini_reply_404_then_pick_model_and_succeed(monkeypatch):
    # First post -> 404, then requests.get returns models, then second post -> 200
    resp404 = _make_resp(status_code=404, json_data={"error": "no model"}, text="404")
    resp200 = _make_resp(status_code=200, json_data={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    calls = {"n": 0}

    def fake_post(*_a, **_k):
        calls["n"] += 1
        return resp404 if calls["n"] == 1 else resp200

    # list models returns one compatible model
    def fake_get(*_a, **_k):
        return _make_resp(status_code=200, json_data={
            "models": [
                {"name": "models/gemini-test", "supportedGenerationMethods": ["generateContent"]}
            ]
        })

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)
    monkeypatch.setattr("game.ai.gemini_api.requests.get", fake_get)

    out = gemini_api.generate_gemini_reply(api_key="k", user_message="hola")
    assert out == "ok"
    assert calls["n"] >= 2


def test_list_models_network_error_raises(monkeypatch):
    def fake_get(*_a, **_k):
        raise requests.exceptions.Timeout("timeout")

    monkeypatch.setattr("game.ai.gemini_api.requests.get", fake_get)

    with pytest.raises(gemini_api.GeminiError) as exc:
        gemini_api._list_models(api_key="k", api_version="v1", timeout_seconds=1)

    assert "Error de red" in str(exc.value)


def test_get_or_pick_model_no_models(monkeypatch):
    monkeypatch.setattr("game.ai.gemini_api._list_models", lambda *a, **k: [])

    with pytest.raises(gemini_api.GeminiError) as exc:
        gemini_api._get_or_pick_model(api_key="k", api_version="v1", timeout_seconds=1)

    assert "No se encontró ningún modelo" in str(exc.value)


def test_long_message_payload_is_sent(monkeypatch):
    captured = {"payload": None}

    def fake_post(*_a, **kwargs):
        captured["payload"] = kwargs.get("json")
        return _make_resp(status_code=200, json_data={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)

    long_msg = "x" * 20000
    out = gemini_api.generate_gemini_reply(api_key="k", user_message=long_msg)

    assert out == "ok"
    assert captured["payload"] is not None
    # last content part should contain the long message
    contents = captured["payload"].get("contents")
    assert contents and any(long_msg in (p.get("parts")[-1].get("text") if isinstance(p.get("parts"), list) else False for p in contents))
