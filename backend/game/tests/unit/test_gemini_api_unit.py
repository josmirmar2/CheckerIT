import pytest
import requests

from game.ai import gemini_api


def test_extract_text_from_candidate_basic():
    cand = {"content": {"parts": [{"text": "Hola"}, {"text": "mundo"}]}}
    txt = gemini_api._extract_text_from_candidate(cand)
    assert txt == "Hola\nmundo"


def test_extract_text_from_candidate_missing_parts():
    assert gemini_api._extract_text_from_candidate(None) == ""
    assert gemini_api._extract_text_from_candidate({}) == ""
    assert gemini_api._extract_text_from_candidate({"content": {}}) == ""


def test_generate_gemini_reply_param_validation():
    with pytest.raises(gemini_api.GeminiError):
        gemini_api.generate_gemini_reply(api_key=None, user_message="x", model="models/test")

    with pytest.raises(gemini_api.GeminiError):
        gemini_api.generate_gemini_reply(api_key="k", user_message="   ", model="models/test")

    with pytest.raises(gemini_api.GeminiError):
        gemini_api.generate_gemini_reply(api_key="k", user_message="hi", api_version="bad")


def test_list_models_success_and_http_error(monkeypatch):
    def fake_get_ok(*_a, **_k):
        class R:
            status_code = 200

            def json(self):
                return {"models": [{"name": "models/g1", "supportedGenerationMethods": ["generateContent"]}]}

        return R()

    monkeypatch.setattr("game.ai.gemini_api.requests.get", fake_get_ok)
    models = gemini_api._list_models(api_key="k", api_version="v1", timeout_seconds=1)
    assert isinstance(models, list) and models

    def fake_get_err(*_a, **_k):
        class R:
            status_code = 400

            def json(self):
                return {"error": "bad"}

            @property
            def text(self):
                return "err"

        return R()

    monkeypatch.setattr("game.ai.gemini_api.requests.get", fake_get_err)
    with pytest.raises(gemini_api.GeminiError):
        gemini_api._list_models(api_key="k", api_version="v1", timeout_seconds=1)


def test_pick_model_from_list_scoring(monkeypatch):
    models = [
        {"name": "models/other", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-old", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-flash-latest", "supportedGenerationMethods": ["generateContent"]},
    ]

    monkeypatch.setattr("game.ai.gemini_api._list_models", lambda *a, **k: models)
    picked = gemini_api._pick_model_from_list(api_key="k", api_version="v1", timeout_seconds=1)
    assert "gemini-flash" in picked or "gemini" in picked


def test_get_or_pick_model_uses_cache(monkeypatch):
    gemini_api._CACHED_MODEL_BY_VERSION["vtest"] = "models/cached"
    out = gemini_api._get_or_pick_model(api_key="k", api_version="vtest", timeout_seconds=1)
    assert out == "models/cached"


def test_get_or_pick_model_no_models_raises(monkeypatch):
    gemini_api._CACHED_MODEL_BY_VERSION.pop("v2", None)
    monkeypatch.setattr("game.ai.gemini_api._list_models", lambda *a, **k: [])
    with pytest.raises(gemini_api.GeminiError):
        gemini_api._get_or_pick_model(api_key="k", api_version="v2", timeout_seconds=1)


def test_generate_gemini_reply_404_without_pick_raises(monkeypatch):
    class R404:
        status_code = 404

        def json(self):
            return {"error": "no"}

        @property
        def text(self):
            return "404"

    def fake_post(*_a, **_k):
        return R404()

    monkeypatch.setattr("game.ai.gemini_api.requests.post", fake_post)
    monkeypatch.setattr("game.ai.gemini_api._pick_model_from_list", lambda *a, **k: None)

    with pytest.raises(gemini_api.GeminiHttpError):
        gemini_api.generate_gemini_reply(api_key="k", user_message="hola", model="models/unknown")
