"""Shared agent caller: sends the conversation to the LLM and reads its JSON decision.

Each domain supplies its own system prompt and action list (domains/<name>/agent_prompt.py).
The baseline agents in this repo are stand-ins written for this project, not any vendor's product.
"""
from __future__ import annotations

import json

from . import llm


def respond(history: list[dict], system: str, actions: set, model: str = llm.DEFAULT_MODEL) -> dict:
    """history: list of {"role": "user"|"model", "text": str}. Returns parsed reply + latency."""
    r = llm.generate(history, system=system, temperature=0.0, model=model)
    try:
        j = llm.parse_json(r["text"])
        if isinstance(j, list):
            j = j[0]
        action = j.get("action", "continue")
        if action not in actions:
            action = "continue"
        out = {"reply": str(j.get("reply", "")), "action": action, "captured": j.get("captured") or {}}
    except Exception:  # noqa: BLE001
        out = {"reply": r["text"][:500], "action": "continue", "captured": {}, "parse_error": True}
    out["latency_s"] = r["latency_s"]
    out["raw"] = r["text"]
    return out


def model_turn_text(out: dict) -> str:
    """How an agent turn is stored in the history (the JSON it produced)."""
    return json.dumps({"reply": out["reply"], "action": out["action"], "captured": out["captured"]}, ensure_ascii=False)
