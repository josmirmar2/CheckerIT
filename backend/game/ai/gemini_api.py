import requests
import time
import random


class GeminiError(RuntimeError):
    pass


class GeminiHttpError(GeminiError):
    def __init__(self, status_code: int, payload: object):
        self.status_code = int(status_code)
        self.payload = payload
        super().__init__(f"Gemini devolvió {status_code}: {payload}")

_BASE_URL = "https://generativelanguage.googleapis.com"
_CACHED_MODEL_BY_VERSION: dict[str, str] = {}


def _extract_text_from_candidate(candidate: dict) -> str:
    content = (candidate or {}).get("content") or {}
    parts = content.get("parts") or []
    texts: list[str] = []
    for part in parts:
        text = (part or {}).get("text")
        if text:
            texts.append(text)
    return "\n".join(texts).strip()


def generate_gemini_reply(
    *,
    api_key: str,
    user_message: str,
    model: str | None = None,
    history: list[dict] | None = None,
    timeout_seconds: int = 15,
    api_version: str = "v1",
    max_retries: int = 2,
    retry_backoff_seconds: float = 0.6,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> str:
    """Genera una respuesta con Gemini via REST API.

    `history` debe venir en formato Gemini `contents`:
    [{"role": "user"|"model", "parts": [{"text": "..."}]}]
    """
    if not api_key:
        raise GeminiError("GEMINI_API_KEY no está configurada")
    if not user_message or not str(user_message).strip():
        raise GeminiError("El mensaje no puede estar vacío")

    contents: list[dict] = []
    if history:
        contents.extend(history)
    contents.append({"role": "user", "parts": [{"text": str(user_message)}]})


    api_version = (api_version or "v1").strip()
    if api_version not in {"v1", "v1beta"}:
        raise GeminiError("GEMINI_API_VERSION debe ser 'v1' o 'v1beta'")

    if not model:
        model = _get_or_pick_model(api_key=api_key, api_version=api_version, timeout_seconds=timeout_seconds)

    model_name = model.strip()
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    def _post_generate(model_path: str):
        url = f"{_BASE_URL}/{api_version}/{model_path}:generateContent"
        try:
            payload: dict = {"contents": contents}

            if system_prompt and str(system_prompt).strip():
                payload["systemInstruction"] = {
                    "role": "system",
                    "parts": [{"text": str(system_prompt)}],
                }

            generation_config: dict = {}
            if temperature is not None:
                try:
                    generation_config["temperature"] = float(temperature)
                except Exception:
                    pass
            if max_output_tokens is not None:
                try:
                    generation_config["maxOutputTokens"] = int(max_output_tokens)
                except Exception:
                    pass
            if generation_config:
                payload["generationConfig"] = generation_config

            return requests.post(
                url,
                params={"key": api_key},
                json=payload,
                timeout=timeout_seconds,
            )
        except requests.RequestException as exc:
            raise GeminiError(f"Error de red llamando a Gemini: {exc}") from exc

    def _request_with_retries(model_path: str):
        nonlocal max_retries, retry_backoff_seconds
        try:
            max_retries = int(max_retries)
        except Exception:
            max_retries = 2
        if max_retries < 0:
            max_retries = 0

        try:
            retry_backoff_seconds = float(retry_backoff_seconds)
        except Exception:
            retry_backoff_seconds = 0.6
        if retry_backoff_seconds < 0:
            retry_backoff_seconds = 0.0

        retryable_statuses = {429, 500, 502, 503, 504}

        last_resp = None
        for attempt in range(max_retries + 1):
            resp = _post_generate(model_path)
            last_resp = resp

            # 404 se gestiona fuera (para auto-selección de modelo)
            if resp.status_code in retryable_statuses:
                if attempt >= max_retries:
                    return resp

                # Backoff exponencial con jitter suave
                sleep_s = retry_backoff_seconds * (2 ** attempt)
                sleep_s = sleep_s * random.uniform(0.8, 1.2)
                if sleep_s > 0:
                    time.sleep(sleep_s)
                continue

            return resp

        return last_resp

    resp = _request_with_retries(model_name)

    # Si el modelo configurado no existe/no soporta generateContent, intenta auto-seleccionar.
    if resp.status_code == 404:
        try:
            data_404 = resp.json()
        except Exception:
            data_404 = {"raw": resp.text}

        picked = _pick_model_from_list(api_key=api_key, api_version=api_version, timeout_seconds=timeout_seconds)
        if picked and picked != model_name:
            _CACHED_MODEL_BY_VERSION[api_version] = picked
            resp = _request_with_retries(picked)
        else:
            raise GeminiHttpError(404, data_404)

    # Errores HTTP con payload útil
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        raise GeminiHttpError(resp.status_code, data)

    try:
        data = resp.json()
    except Exception as exc:
        raise GeminiError(f"Respuesta JSON inválida desde Gemini: {exc}") from exc

    candidates = data.get("candidates") or []
    if not candidates:
        raise GeminiError(f"Gemini no devolvió candidatos: {data}")

    text = _extract_text_from_candidate(candidates[0])
    if not text:
        raise GeminiError(f"Gemini devolvió una respuesta vacía: {data}")

    return text


def _list_models(*, api_key: str, api_version: str, timeout_seconds: int) -> list[dict]:
    url = f"{_BASE_URL}/{api_version}/models"
    try:
        resp = requests.get(url, params={"key": api_key}, timeout=timeout_seconds)
    except requests.RequestException as exc:
        raise GeminiError(f"Error de red listando modelos de Gemini: {exc}") from exc

    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        raise GeminiError(f"No se pudo listar modelos ({resp.status_code}): {data}")

    try:
        data = resp.json()
    except Exception as exc:
        raise GeminiError(f"Respuesta JSON inválida listando modelos: {exc}") from exc

    return data.get("models") or []


def _pick_model_from_list(*, api_key: str, api_version: str, timeout_seconds: int) -> str | None:
    models = _list_models(api_key=api_key, api_version=api_version, timeout_seconds=timeout_seconds)

    def supports_generate(m: dict) -> bool:
        methods = m.get("supportedGenerationMethods") or []
        return "generateContent" in methods

    candidates = [m for m in models if supports_generate(m)]
    if not candidates:
        return None

    # Preferencia: flash > resto
    def score(m: dict) -> tuple[int, int, int]:
        name = (m.get("name") or "").lower()
        return (
            1 if "gemini" in name else 0,
            1 if "flash" in name else 0,
            1 if "latest" in name else 0,
        )

    candidates.sort(key=score, reverse=True)
    picked = candidates[0].get("name")
    return str(picked) if picked else None


def _get_or_pick_model(*, api_key: str, api_version: str, timeout_seconds: int) -> str:
    cached = _CACHED_MODEL_BY_VERSION.get(api_version)
    if cached:
        return cached

    picked = _pick_model_from_list(api_key=api_key, api_version=api_version, timeout_seconds=timeout_seconds)
    if not picked:
        raise GeminiError(
            "No se encontró ningún modelo compatible con generateContent. "
            "Prueba a cambiar GEMINI_API_VERSION o revisa tu API key."
        )

    _CACHED_MODEL_BY_VERSION[api_version] = picked
    return picked
