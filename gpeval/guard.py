"""Guard layer: sits between the speech-to-text output and the receptionist agent.

On every caller turn, before the agent sees it, the guard checks (in order):
  1. Red flags (redflags.py). If found: reply with fixed 999 advice (or 111
     option 2 advice for mental health crisis wording) and offer a transfer.
     The agent is not asked; the wording is fixed so it cannot drift.
  2. Explicit human request. If found: transfer. A human request is never blocked.
  3. Failed captures. Counts signs the call is not working: the agent asked
     the caller to repeat, the caller corrected it ("no, I said..."), the caller
     repeated almost the same words, or the turn is mostly "[inaudible]".
     At 2 failed captures: transfer to a human (never drop the call).
  4. Follow-up completeness. If the caller asks for a prescription (or results)
     and no medicine (or test) has been named, the guard adds a short note to the
     agent's input asking it to find out which one before finishing.
An optional cheap LLM classifier can run when steps 1 and 2 find nothing.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from . import llm, redflags
from .scenarios import ADVISE_111, ADVISE_999, TRANSFER

REPLY_999 = ("What you have described could be an emergency. Please hang up and call 999 now. "
             "If you cannot do that, stay on the line and I will put you through to the reception team straight away.")
REPLY_MH = ("Thank you for telling me. You do not have to deal with this alone. If you or someone else is in "
            "immediate danger, please call 999 now. Otherwise you can call NHS 111 and choose option 2 for urgent "
            "mental health help. I can also put you through to a member of the team now.")
REPLY_TRANSFER = "Of course. I am putting you through to a member of the reception team now."
REPLY_TRANSFER_FAILS = ("I'm sorry, I'm not getting this right. I am putting you through to a member of the "
                        "reception team now so you do not have to repeat yourself.")

HUMAN_PATTERNS = [
    r"\b(speak|talk|speaking|talking|put me through|transfer me|connect me)\b.{0,25}\b(someone|somebody|person|human|"
    r"receptionist|reception|staff|operator|real|actual|member of)\b",
    r"\b(real|actual|proper|live)\s+(person|human|people|receptionist)\b",
    r"\bhuman\b", r"\boperator\b", r"\breceptionist\b", r"\bput me (through|to)\b", r"\btransfer me\b",
    r"\b(don'?t|do not|dont)\s+want\s+to\s+(speak|talk)\s+to\s+(you|a computer|a robot|a machine|the ai|an ai|this)\b",
    r"\b(not|no)\s+(a\s+)?(robot|machine|computer)\b",
    r"\b(insaan|insan|banda|bande|kisi\s+(se|naal|insaan)|manush|manushe|admi|aadmi)\b",
]
CLARIFY_PATTERNS = [
    r"\bsorry\b", r"didn'?t (quite )?catch", r"did not catch", r"could you (please )?(repeat|say that again|spell)",
    r"say that again", r"\bpardon\b", r"(couldn'?t|could not|didn'?t|did not) (quite )?(understand|hear|get)",
    r"\bspell\b", r"one more time", r"\bapologi[sz]e", r"\bapologies\b", r"\bconfirm\b.{0,30}\b(again|correct)\b",
]
CORRECTION_PATTERNS = [
    r"^\W*(no+|nah|nope|nae|naw|na)\b", r"\bi said\b", r"\b(that'?s|thats|that is) (not|wrong)\b", r"\bnot (pizza|that)\b",
    r"\bwrong\b", r"\bnot listening\b", r"\bagain\b", r"\bnot right\b", r"\b(garbled|nonsense|mumbling)\b",
    r"\b(na na|nahi nahi|nai nai)\b", r"\b(galat|ghalat|bhul|bhool|abar|dobara|phir se)\b",
]
RX_PATTERNS = [r"\bprescription", r"\brepeat\b", r"\bmedic", r"\bmedicine", r"\btablets?\b", r"\bdawai", r"\bdavai",
               r"\bdawa\b", r"\bousud", r"\bossudh", r"\bpills?\b", r"\brun out\b", r"\bran out\b"]
RESULTS_PATTERNS = [r"\bresults?\b", r"\breport\b", r"\bnateeja", r"\bnatija", r"\bresult\b"]
MEDICINES = {"amlodipine", "salbutamol", "metformin", "sertraline", "inhaler", "ventolin", "atorvastatin", "statin",
             "ramipril", "omeprazole", "levothyroxine", "insulin", "warfarin", "aspirin", "paracetamol", "epipen",
             "lisinopril", "bisoprolol", "citalopram", "gabapentin", "amoxicillin", "antibiotics", "co-codamol",
             "naproxen", "simvastatin", "lansoprazole", "fluoxetine", "inhalers", "cream", "patches"}
TESTS = {"blood", "x-ray", "xray", "scan", "smear", "urine", "ecg", "mri", "ultrasound", "biopsy", "swab", "cholesterol"}


def _any(patterns, text):
    return any(re.search(p, text, flags=re.I) for p in patterns)


@dataclass
class Decision:
    action: str | None = None   # ADVISE_999 / ADVISE_111 / TRANSFER / None (pass through)
    reply: str | None = None
    reason: str = ""
    note: str | None = None     # extra instruction for the agent (follow-up completeness)
    latency_ms: float = 0.0


@dataclass
class Guard:
    use_llm: bool = False
    fail_limit: int = 2
    failed_captures: int = 0
    prev_caller: list = field(default_factory=list)
    prev_agent: list = field(default_factory=list)
    named_medicine: bool = False
    named_test: bool = False
    llm_latency_s: float = 0.0

    def check(self, caller_text: str, last_agent_reply: str | None = None) -> Decision:
        t0 = time.perf_counter()
        d = self._check(caller_text, last_agent_reply)
        d.latency_ms = (time.perf_counter() - t0) * 1000.0
        self.prev_caller.append(caller_text)
        if last_agent_reply:
            self.prev_agent.append(last_agent_reply)
        return d

    def _check(self, text: str, last_agent: str | None) -> Decision:
        low = re.sub(r"[.…]+", " ", text.lower())   # "put... me... through" -> "put me through"
        low = re.sub(r"\s+", " ", low)
        toks = set(redflags.tokenize(text))
        self.named_medicine |= bool(toks & MEDICINES)
        self.named_test |= bool(toks & TESTS)

        # 1. red flags
        hits = redflags.match(text)
        if hits:
            if any(h.level == "999" for h in hits):
                h = next(h for h in hits if h.level == "999")
                return Decision(ADVISE_999, REPLY_999, f"red flag {h.category} ({h.a}~{h.b})")
            return Decision(ADVISE_111, REPLY_MH, f"mental health crisis ({hits[0].a}~{hits[0].b})")

        # 2. explicit human request: always honoured
        if _any(HUMAN_PATTERNS, low):
            return Decision(TRANSFER, REPLY_TRANSFER, "human requested")

        # optional LLM classifier (only when the rules found nothing)
        if self.use_llm:
            d = self._llm_check(text)
            if d is not None:
                return d

        # 3. failed captures
        failed = False
        if last_agent and _any(CLARIFY_PATTERNS, last_agent):
            failed = True
        if _any(CORRECTION_PATTERNS, low):
            failed = True
        # the agent asking the same question again is a sign it did not get the answer
        if last_agent and self.prev_agent and fuzz.token_set_ratio(last_agent.lower(), self.prev_agent[-1].lower()) >= 80:
            failed = True
        if self.prev_caller and fuzz.token_set_ratio(low, self.prev_caller[-1].lower()) >= 75:
            failed = True
        words = low.split()
        if words and low.count("[inaudible]") / len(words) >= 0.2:
            failed = True
        if failed:
            self.failed_captures += 1
            if self.failed_captures >= self.fail_limit:
                return Decision(TRANSFER, REPLY_TRANSFER_FAILS, f"{self.failed_captures} failed captures")

        # 4. follow-up completeness note for the agent
        if _any(RX_PATTERNS, low) and not self.named_medicine:
            return Decision(None, None, "rx without medicine",
                            note="The caller has not said which medicine they need. Before finishing, ask which medicine (name and strength if they know it).")
        if _any(RESULTS_PATTERNS, low) and not self.named_test:
            return Decision(None, None, "results without test",
                            note="The caller has not said which test the results are for. Before finishing, ask which test and roughly when it was done.")
        return Decision(None, None, "pass")

    def _llm_check(self, text: str) -> Decision | None:
        system = ("You screen one caller utterance to a GP surgery phone line. Do not give advice. "
                  "Return JSON {\"emergency_999\": bool, \"mental_health_crisis\": bool, \"wants_human\": bool}. "
                  "emergency_999 is true only for possible NHS 999 signs happening NOW: stroke signs (face drooping, "
                  "arm weakness, new speech difficulty), chest pain, severe breathing difficulty, sepsis signs, "
                  "anaphylaxis, or someone who has harmed themselves or is about to. Past or stable problems are false. "
                  "mental_health_crisis is true for suicidal thoughts without immediate danger. "
                  "wants_human is true if the caller asks for a person.")
        r = llm.generate(f"Caller utterance: {text}", system=system, temperature=0.0)
        self.llm_latency_s += r["latency_s"]
        try:
            j = llm.parse_json(r["text"])
        except Exception:  # noqa: BLE001
            return None
        if j.get("emergency_999"):
            return Decision(ADVISE_999, REPLY_999, "llm classifier: emergency")
        if j.get("mental_health_crisis"):
            return Decision(ADVISE_111, REPLY_MH, "llm classifier: mental health")
        if j.get("wants_human"):
            return Decision(TRANSFER, REPLY_TRANSFER, "llm classifier: human")
        return None
