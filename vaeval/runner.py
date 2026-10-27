"""Play each transcript through a domain's baseline agent, with or without the guard.

Caller turns are scripted (they do not react to the agent). For each caller
turn: (guard check, if on) -> agent reply -> stop if the call was escalated,
transferred or ended. The outcome of the call is the first terminal action,
or the domain's ROUTINE action if none happened.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from . import agent
from .followup import asked_for
from .guard import Guard

MODES = ("baseline", "guard", "guard_llm")


def run_call(row: dict, mode: str, dom) -> dict:
    history: list[dict] = []
    guard = Guard(dom.GUARD_CONFIG, use_llm=(mode == "guard_llm"), context=dom.guard_context(row)) if mode != "baseline" else None
    system = dom.agent_system(row)
    final_action, final_turn, decided_by, reason = dom.ROUTINE, None, "none", ""
    agent_replies: list[str] = []
    turn_log = []
    agent_latency, n_agent_calls = 0.0, 0
    guard_ms: list[float] = []
    last_reply = None
    for i, text in enumerate(row["turns"]):
        user_text = text
        d = None
        if guard is not None:
            d = guard.check(text, last_reply)
            guard_ms.append(d.latency_ms)
            if d.action:
                final_action, final_turn, decided_by, reason = d.action, i, "guard", d.reason
                agent_replies.append(d.reply)
                turn_log.append({"caller": text, "guard": d.reason, "reply": d.reply, "action": d.action})
                break
            if d.note:
                user_text = dom.NOTE_TEMPLATE.format(text=text, note=d.note)
        history.append({"role": "user", "text": user_text})
        out = agent.respond(history, system, dom.AGENT_ACTIONS, model=dom.AGENT_MODEL)
        n_agent_calls += 1
        agent_latency += out["latency_s"]
        history.append({"role": "model", "text": agent.model_turn_text(out)})
        agent_replies.append(out["reply"])
        last_reply = out["reply"]
        turn_log.append({"caller": user_text, "guard": None if d is None else d.reason,
                         "reply": out["reply"], "action": out["action"]})
        if out["action"] in dom.TERMINAL:
            final_action, final_turn, decided_by = out["action"], i, "agent"
            break

    followups = row.get("followups") or []
    fu_asked = all(asked_for(f, agent_replies, dom.ASK_PATTERNS) for f in followups) if followups else None
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


def run_all(rows: list[dict], mode: str, dom, workers: int = 2) -> list[dict]:
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda r: run_call(r, mode, dom), rows))
