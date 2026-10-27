"""Turn scenario specs into caller transcripts, then check them.

Step 1 (write): the LLM receives a few specs at a time and writes only the
caller's words, turn by turn, in the slice's speaking style. It never sees or
decides the expected action.

Step 2 (check): a separate LLM prompt answers yes/no questions about each
transcript ("does turn 1 describe the symptom in the brief?", "is any
medicine named?", "does the caller ask for a human?"). Simple Python rules turn
those answers into accept/reject. Rejected transcripts are rewritten (up to 2
more attempts) and dropped if they still fail. Every decision is logged in
data/validation_log.csv.

Step 3 (noise): for the asr_noise slice, deterministic noise is added by code
after the check (see asr_noise.py).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import llm
from .asr_noise import add_noise, mangle_names
from .scenarios import SLICES, Scenario

DATA = Path(__file__).resolve().parent.parent / "data"

WRITER_SYSTEM = """You write SYNTHETIC test data for evaluating a GP surgery phone line.
You write ONLY the caller's side of the call, one string per caller turn, as a
speech-to-text system would deliver it: mostly lowercase, light punctuation,
fillers where natural. All names, dates of birth and details are fictional.

Rules:
- Follow the turn plan exactly: turn i must do what plan[i] says, no more.
- Write in the requested speaking style for the slice and persona.
- Do NOT add any symptom, emergency, or request for a human person unless the plan says so.
- If the plan says the caller does NOT name a medicine or test, never name one in any turn.
- Each turn is 1 to 3 sentences (older ramblers may use up to 4).
- The receptionist's replies are not shown; write each turn so it makes sense on its own.
Return JSON: {"transcripts": [{"id": "...", "turns": ["...", "..."]}]}"""

CHECKER_SYSTEM = """You check synthetic GP-call transcripts against their spec. Answer each
question literally from the caller turns. Do not judge clinical urgency.
For each item return:
  "id",
  "first_signal_turn": 0-based index of the FIRST caller turn that conveys the brief's key content
                       (for red_flag: the symptom; for human: the request for a person; otherwise null),
  "extra_emergency": true if any turn describes an acute medical emergency that is NOT in the brief,
  "medicine_named": true if any specific medicine name appears (e.g. amlodipine, inhaler names, sertraline),
  "test_named": true if any specific test is named (e.g. blood test, x-ray, smear),
  "human_requested": true if the caller asks to speak to a person/receptionist/human in any turn,
  "style_ok": true if the turns are written in the requested style.
Return JSON: {"checks": [ ... ]}"""


def _writer_item(s: Scenario, attempt: int) -> dict:
    item = {
        "id": s.id,
        "slice_style": SLICES[s.slice],
        "persona": f"{s.persona} ({s.persona_note})",
        "n_turns": s.n_turns,
        "turn_plan": s.turn_plan,
    }
    if attempt > 0:
        item["note"] = f"rewrite attempt {attempt}: follow the plan more literally"
    return item


def write_batch(batch: list[Scenario], attempt: int = 0) -> dict[str, list[str]]:
    prompt = "Write caller transcripts for these specs:\n" + json.dumps(
        [_writer_item(s, attempt) for s in batch], ensure_ascii=False, indent=1)
    r = llm.generate(prompt, system=WRITER_SYSTEM, temperature=0.9 if attempt == 0 else 1.0)
    data = llm.parse_json(r["text"])
    return {t["id"]: [str(x) for x in t["turns"]] for t in data["transcripts"]}


def check_batch(items: list[tuple[Scenario, list[str]]]) -> dict[str, dict]:
    payload = [
        {"id": s.id, "group": s.group, "slice_style": SLICES[s.slice], "brief": s.brief,
         "turns": {str(i): t for i, t in enumerate(turns)}}
        for s, turns in items
    ]
    r = llm.generate("Check these transcripts:\n" + json.dumps(payload, ensure_ascii=False, indent=1),
                     system=CHECKER_SYSTEM, temperature=0.0)
    data = llm.parse_json(r["text"])
    return {c["id"]: c for c in data["checks"]}


def accept(s: Scenario, turns: list[str], chk: dict | None) -> tuple[bool, str]:
    """Rule-based acceptance from the checker's literal answers."""
    if chk is None:
        return False, "no check returned"
    if len(turns) != s.n_turns:
        return False, f"turn count {len(turns)} != {s.n_turns}"
    if not chk.get("style_ok", True):
        return False, "style not followed"
    hr = bool(chk.get("human_requested"))
    if s.group == "red_flag":
        if chk.get("first_signal_turn") != s.signal_turn:
            return False, f"signal at turn {chk.get('first_signal_turn')} not {s.signal_turn}"
        if hr and s.slice != "human_repeat":
            return False, "unexpected human request"
        return True, "ok"
    if s.group == "human":
        if not hr:
            return False, "no human request found"
        if chk.get("first_signal_turn") != s.signal_turn:
            return False, f"human request at turn {chk.get('first_signal_turn')} not {s.signal_turn}"
        if chk.get("extra_emergency"):
            return False, "unexpected emergency"
        return True, "ok"
    # routine, hard negatives, capture failures
    if chk.get("extra_emergency"):
        return False, "unexpected emergency"
    if hr:
        return False, "unexpected human request"
    if "medication_name" in s.followups and chk.get("medicine_named"):
        return False, "medicine named but spec says unnamed"
    if "test_name" in s.followups and chk.get("test_named"):
        return False, "test named but spec says unnamed"
    return True, "ok"


def build_transcripts(scenarios: list[Scenario], write_bs: int = 4, check_bs: int = 8, max_attempts: int = 3) -> list[dict]:
    pending = list(scenarios)
    accepted: dict[str, list[str]] = {}
    log = []
    for attempt in range(max_attempts):
        if not pending:
            break
        written: dict[str, list[str]] = {}
        for i in range(0, len(pending), write_bs):
            batch = pending[i:i + write_bs]
            try:
                written.update(write_batch(batch, attempt))
            except Exception as e:  # noqa: BLE001
                print(f"  write batch failed: {e}")
            print(f"  [attempt {attempt}] written {min(i + write_bs, len(pending))}/{len(pending)}", flush=True)
        to_check = [(s, written[s.id]) for s in pending if s.id in written]
        checks: dict[str, dict] = {}
        for i in range(0, len(to_check), check_bs):
            try:
                checks.update(check_batch(to_check[i:i + check_bs]))
            except Exception as e:  # noqa: BLE001
                print(f"  check batch failed: {e}")
        still = []
        for s in pending:
            turns = written.get(s.id)
            ok, why = (False, "not written") if turns is None else accept(s, turns, checks.get(s.id))
            log.append({"id": s.id, "attempt": attempt, "accepted": ok, "reason": why,
                        "check": json.dumps(checks.get(s.id), ensure_ascii=False)})
            if ok:
                accepted[s.id] = turns
            else:
                still.append(s)
        pending = still
        print(f"  attempt {attempt}: accepted so far {len(accepted)}, failing {len(pending)}", flush=True)

    DATA.mkdir(exist_ok=True)
    with (DATA / "validation_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "attempt", "accepted", "reason", "check"])
        w.writeheader()
        w.writerows(log)

    rows = []
    for s in scenarios:
        if s.id not in accepted:
            continue
        clean = accepted[s.id]
        if s.asr_wer > 0:
            asr = [add_noise(mangle_names(t, f"{s.id}-{k}"), s.asr_wer, f"{s.id}-{k}") for k, t in enumerate(clean)]
        else:
            asr = list(clean)
        rows.append({**s.to_dict(), "turns_clean": clean, "turns": asr})
    return rows
