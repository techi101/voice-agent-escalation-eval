"""GP clinic prompts for the transcript writer and checker, and the accept rules.

The writer LLM writes only the caller's words. The checker LLM answers literal
yes/no questions. accept() turns those answers into accept/reject with plain code.
"""
from vaeval.scenario import Scenario

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
