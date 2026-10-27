"""Small Gemini wrapper: disk cache + retry with backoff.

Every response is stored in cache/llm_cache.jsonl, keyed by a SHA-256 hash of
(model, system prompt, contents, settings). A rerun with the same inputs reads
the cache and makes no network call, so results are reproducible and free.
The API key is read from the GEMINI_API_KEY environment variable and is never
printed or written anywhere.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "cache" / "llm_cache.jsonl"
DEFAULT_MODEL = os.environ.get("VAEVAL_MODEL", "gemini-3.5-flash-lite")

_lock = threading.Lock()
_cache: dict[str, dict] | None = None
_client = None
STATS = {"network_calls": 0, "cache_hits": 0, "retries": 0}


def _load_cache() -> dict[str, dict]:
    global _cache
    with _lock:  # threads must not see a half-loaded cache (that caused spurious cache misses)
        if _cache is None:
            loaded = {}
            if CACHE_PATH.exists():
                with CACHE_PATH.open(encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            rec = json.loads(line)
                            loaded[rec["key"]] = rec
            _cache = loaded
    return _cache


def _get_client():
    global _client
    if _client is None:
        from google import genai  # imported lazily so tests run without the SDK

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set and the response is not in the cache.")
        _client = genai.Client(api_key=key)
    return _client


def cache_key(model: str, system: str, contents: list[dict], json_mode: bool, temperature: float) -> str:
    payload = json.dumps(
        {"model": model, "system": system, "contents": contents, "json": json_mode, "t": temperature},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate(
    contents: list[dict] | str,
    system: str = "",
    model: str = DEFAULT_MODEL,
    json_mode: bool = True,
    temperature: float = 0.0,
    max_retries: int = 8,
    offline: bool = False,
) -> dict:
    """Return {"text": str, "latency_s": float, "cached": bool}.

    contents: a plain string, or a list of {"role": "user"|"model", "text": str}.
    latency_s is the latency of the ORIGINAL network call (stored in the cache),
    so reported latencies stay stable across reruns.
    """
    if isinstance(contents, str):
        contents = [{"role": "user", "text": contents}]
    key = cache_key(model, system, contents, json_mode, temperature)
    cache = _load_cache()
    if key in cache:
        STATS["cache_hits"] += 1
        rec = cache[key]
        return {"text": rec["text"], "latency_s": rec["latency_s"], "cached": True}
    if offline or os.environ.get("VAEVAL_OFFLINE") == "1":
        raise KeyError("offline mode: response not cached")

    from google.genai import types

    client = _get_client()
    cfg = types.GenerateContentConfig(
        system_instruction=system or None,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )
    sdk_contents = [
        types.Content(role=c["role"], parts=[types.Part(text=c["text"])]) for c in contents
    ]
    delay = 5.0
    for attempt in range(max_retries + 1):
        t0 = time.perf_counter()
        try:
            resp = client.models.generate_content(model=model, contents=sdk_contents, config=cfg)
            latency = time.perf_counter() - t0
            text = resp.text or ""
            break
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            transient = any(s in msg for s in ("429", "RESOURCE_EXHAUSTED", "503", "500", "UNAVAILABLE", "DEADLINE", "timed out"))
            if not transient or attempt == max_retries:
                raise
            STATS["retries"] += 1
            sleep_s = delay + random.uniform(0, 2)
            print(f"  [llm] transient error ({msg[:60]}...), retry {attempt + 1} in {sleep_s:.0f}s", flush=True)
            time.sleep(sleep_s)
            delay = min(delay * 2, 120)
    STATS["network_calls"] += 1
    rec = {"key": key, "model": model, "text": text, "latency_s": round(latency, 3), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with _lock:
        cache[key] = rec
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"text": text, "latency_s": rec["latency_s"], "cached": False}


def parse_json(text: str):
    """Parse a JSON reply, tolerating ```json fences."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    return json.loads(t)
