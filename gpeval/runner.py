"""Play each transcript through the baseline agent, with or without the guard.

Caller turns are scripted (they do not react to the agent). For each caller
turn: (guard check, if on) -> agent reply -> stop if the call was escalated or
transferred. The outcome of the call is the first escalation/transfer action,
or "routine" if none happened.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from . import agent
from .followup import asked_for
from .guard import Guard
from .scenarios import ROUTINE

MODES = ("baseline", "guard", "guard_llm")


def run_call(row: dict, mode: str) -> dict:
    history: list[dict] = []
    guard = Guard(use_llm=(mode == "guard_llm")) if mode != "baseline" else None
    final_action, final_turn, decided_by, reason = ROUTINE, None, "none", ""
    agent_replies: list[str] = []
    turn_log = []
    agent_latency, n_agent_calls = 0.0, 0
    guard_ms: list[float] = []
    last_reply = None
    for i, text in enumerate(row["turns"]):
        user_text = text
        if guard is not None:
            d = guard.check(text, last_reply)
            guard_ms.append(d.latency_ms)
            if d.action:
                final_action, final_turn, decided_by, reason = d.action, i, "guard", d.reason
                agent_replies.append(d.reply)
                turn_log.append({"caller": text, "guard": d.reason, "reply": d.reply, "action": d.action})
                break
            if d.note:
                user_text = f"{text}\n\n[Call-checking layer note to the receptionist: {d.note}]"
        history.append({"role": "user", "text": user_text})
        out = agent.respond(history)
        n_agent_calls += 1
        agent_latency += out["latency_s"]
        history.append({"role": "model", "text": agent.model_turn_text(out)})
        agent_replies.append(out["reply"])
        last_reply = out["reply"]
        turn_log.append({"caller": user_text, "guard": None if guard is None else d.reason,
                         "reply": out["reply"], "action": out["action"]})
        if out["action"] in agent.TERMINAL:
            final_action, final_turn, decided_by = out["action"], i, "agent"
            break

    followups = row.get("followups") or []
    fu_asked = all(asked_for(f, agent_replies) for f in followups) if followups else None
    return {
        "id": row["id"], "slice": row["slice"], "group": row["group"], "kind": row["kind"], "split": row["split"],
        "mode": mode, "expected": row["expected"], "acceptable": "|".join(row["acceptable"]),
        "final_action": final_action, "final_turn": final_turn, "decided_by": decided_by, "guard_reason": reason,
        "correct": final_action in row["acceptable"],
        "signal_turn": row["signal_turn"], "handoff_by_turn": row["handoff_by_turn"],
        "followups": "|".join(followups), "followup_asked": fu_asked,
        "n_agent_calls": n_agent_calls, "agent_latency_s": round(agent_latency, 3),
        "guard_ms_turns": json.dumps([round(x, 3) for x in guard_ms]),
        "guard_llm_latency_s": round(guard.llm_latency_s, 3) if guard else 0.0,
        "turns_heard": (final_turn + 1) if final_turn is not None else len(row["turns"]),
        "log": json.dumps(turn_log, ensure_ascii=False),
    }


def run_all(rows: list[dict], mode: str, workers: int = 4) -> list[dict]:
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda r: run_call(r, mode), rows))
