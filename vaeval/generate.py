"""Turn scenario specs into caller transcripts, then check them (shared by all domains).

Step 1 (write): the LLM receives a few specs at a time and writes only the
caller's words, turn by turn, in the slice's speaking style. It never sees or
decides the expected action. The prompt comes from the domain (writer.py).

Step 2 (check): a separate LLM prompt answers literal yes/no questions about
each transcript. The domain's accept() turns those answers into accept/reject.
Rejected transcripts are rewritten (up to 2 more attempts) and dropped if they
still fail. Every decision is logged in data/<domain>/validation_log.csv.

Step 3 (noise): for slices with asr_wer > 0, deterministic noise is added by
code after the check (see asr_noise.py).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import llm
from .asr_noise import add_noise, mangle_names
from .scenario import Scenario


def _writer_item(s: Scenario, attempt: int, slices: dict) -> dict:
    item = {
        "id": s.id,
        "slice_style": slices[s.slice],
        "persona": f"{s.persona} ({s.persona_note})",
        "n_turns": s.n_turns,
        "turn_plan": s.turn_plan,
    }
    if attempt > 0:
        item["note"] = f"rewrite attempt {attempt}: follow the plan more literally"
    return item


def write_batch(dom, batch: list[Scenario], attempt: int = 0) -> dict[str, list[str]]:
    prompt = "Write caller transcripts for these specs:\n" + json.dumps(
        [_writer_item(s, attempt, dom.SLICES) for s in batch], ensure_ascii=False, indent=1)
    r = llm.generate(prompt, system=dom.WRITER_SYSTEM, temperature=0.9 if attempt == 0 else 1.0,
                     model=getattr(dom, "WRITER_MODEL", llm.DEFAULT_MODEL))
    data = llm.parse_json(r["text"])
    return {t["id"]: [str(x) for x in t["turns"]] for t in data["transcripts"]}


def check_batch(dom, items: list[tuple[Scenario, list[str]]]) -> dict[str, dict]:
    payload = [
        {"id": s.id, "group": s.group, "slice_style": dom.SLICES[s.slice], "brief": s.brief,
         "turns": {str(i): t for i, t in enumerate(turns)}}
        for s, turns in items
    ]
    r = llm.generate("Check these transcripts:\n" + json.dumps(payload, ensure_ascii=False, indent=1),
                     system=dom.CHECKER_SYSTEM, temperature=0.0, model=getattr(dom, "WRITER_MODEL", llm.DEFAULT_MODEL))
    data = llm.parse_json(r["text"])
    return {c["id"]: c for c in data["checks"]}


def build_transcripts(dom, scenarios: list[Scenario], data_dir: Path, write_bs: int = 4, check_bs: int = 8,
                      max_attempts: int = 3) -> list[dict]:
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
                written.update(write_batch(dom, batch, attempt))
            except Exception as e:  # noqa: BLE001
                print(f"  write batch failed: {e}")
            print(f"  [attempt {attempt}] written {min(i + write_bs, len(pending))}/{len(pending)}", flush=True)
        to_check = [(s, written[s.id]) for s in pending if s.id in written]
        checks: dict[str, dict] = {}
        for i in range(0, len(to_check), check_bs):
            try:
                checks.update(check_batch(dom, to_check[i:i + check_bs]))
            except Exception as e:  # noqa: BLE001
                print(f"  check batch failed: {e}")
        still = []
        for s in pending:
            turns = written.get(s.id)
            ok, why = (False, "not written") if turns is None else dom.accept(s, turns, checks.get(s.id))
            log.append({"id": s.id, "attempt": attempt, "accepted": ok, "reason": why,
                        "check": json.dumps(checks.get(s.id), ensure_ascii=False)})
            if ok:
                accepted[s.id] = turns
            else:
                still.append(s)
        pending = still
        print(f"  attempt {attempt}: accepted so far {len(accepted)}, failing {len(pending)}", flush=True)

    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "validation_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "attempt", "accepted", "reason", "check"])
        w.writeheader()
        w.writerows(log)

    rows = []
    for s in scenarios:
        if s.id not in accepted:
            continue
        clean = accepted[s.id]
        if s.asr_wer > 0:
            asr = [add_noise(mangle_names(t, f"{s.id}-{k}", dom.NAMES_TO_MANGLE, dom.CONFUSIONS), s.asr_wer,
                             f"{s.id}-{k}", dom.CONFUSIONS) for k, t in enumerate(clean)]
        else:
            asr = list(clean)
        rows.append({**s.to_dict(), "turns_clean": clean, "turns": asr})
    return rows
