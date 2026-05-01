import json
import hashlib
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.cache import cache


DEFAULT_CACHE_TIMEOUT = 60 * 60 * 24


def is_rate_limited(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False

    error = str(payload.get("error", "")).lower()
    detail = str(payload.get("detail", "")).lower()
    status = payload.get("status")

    return (
        status == 429
        or "too many requests" in error
        or "too many requests" in detail
        or detail.startswith("http 429")
    )


def openf1_cache_key(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"openf1:{digest}"


def openf1_json(
    url: str,
    *,
    timeout: int = DEFAULT_CACHE_TIMEOUT,
    retries: int = 0,
    retry_delay: float = 1.0,
):
    cache_key = openf1_cache_key(url)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    last_payload = None

    for attempt in range(retries + 1):
        payload = _fetch_openf1_json(url)
        last_payload = payload

        if is_rate_limited(payload):
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            return payload

        cache.set(cache_key, payload, timeout=timeout)
        return payload

    return last_payload


def _fetch_openf1_json(url: str):
    request = Request(url, headers={"User-Agent": "F1RaceViewer/1.0"})

    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
            payload = json.loads(body)
        except Exception:
            payload = {"detail": f"HTTP {exc.code}"}

        if not isinstance(payload, dict):
            payload = {"detail": payload}

        payload.setdefault("status", exc.code)
        if exc.code == 429:
            payload.setdefault("error", "Too Many Requests")

        return payload
    except URLError as exc:
        return {"detail": str(exc.reason), "status": 503}
