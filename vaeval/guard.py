"""Guard layer engine, shared by all domains. Each domain supplies a GuardConfig.

The guard sits between the speech-to-text output and the agent. On every
caller turn, before the agent sees it, it checks (in order):
  0. Pre-call policy (optional, e.g. collections: no recovery calls outside
     8 AM to 7 PM). Checked on the first turn only.
  1. Must-escalate rules (vaeval/matcher.py with the domain's word lists).
     If found: reply with fixed wording; the agent is not asked.
  2. Pattern stages, in the domain's order (e.g. explicit human request, which
     is never blocked; "stop calling"; "wrong number"; "already paid").
  3. Optional LLM classifier, only when 1 and 2 found nothing.
  4. Failed captures: the agent asked the caller to repeat, the caller
     corrected it, the caller repeated nearly the same words, the agent asked
     the same question again, or the turn is mostly "[inaudible]".
     At `fail_limit` (2) failed captures: transfer to a human, never drop the call.
  5. Follow-up completeness: if the request needs a field nobody has given
     (medicine name, payment amount, payment date...), add a short note to the
     agent's input asking it to find out before finishing.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable

from rapidfuzz import fuzz

from . import llm
from .matcher import Matcher, tokenize


def any_match(patterns, text) -> bool:
    return any(re.search(p, text, flags=re.I) for p in patterns)


@dataclass
class PatternStage:
    name: str           # reason shown in results, e.g. "human requested"
    patterns: list
    action: str
    reply: str


@dataclass
class FollowupCheck:
    field: str
    trigger_patterns: list           # the request that needs this field
    note: str                        # instruction added to the agent's input
    named_tokens: set | None = None  # the field counts as given if any of these words appear...
    named_patterns: list | None = None  # ...or any of these regexes match


@dataclass
class GuardConfig:
    matcher: Matcher
    level_actions: dict              # level -> (action, reply, reason format using {cat} {a} {b})
    level_priority: list             # which level wins if several fire
    stages: list                     # PatternStage list, checked in order after the rules
    clarify_patterns: list
    correction_patterns: list
    transfer_action: str
    reply_transfer_fails: str
    followups: list = field(default_factory=list)
    precheck: Callable[[dict], tuple | None] | None = None   # context -> (action, reply, reason) or None
    llm_system: str | None = None    # optional classifier prompt
    llm_labels: dict = field(default_factory=dict)          # json key -> (action, reply, reason)
    llm_model: str = "gemma-4-26b-a4b-it"
    fail_limit: int = 2


@dataclass
class Decision:
    action: str | None = None   # an escalation/transfer action, or None (pass through)
    reply: str | None = None
    reason: str = ""
    note: str | None = None     # extra instruction for the agent (follow-up completeness)
    latency_ms: float = 0.0


@dataclass
class Guard:
    cfg: GuardConfig
    use_llm: bool = False
    context: dict = field(default_factory=dict)
    failed_captures: int = 0
    prev_caller: list = field(default_factory=list)
    prev_agent: list = field(default_factory=list)
    named: dict = field(default_factory=dict)
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
        cfg = self.cfg
        low = re.sub(r"[.…]+", " ", text.lower())   # "put... me... through" -> "put me through"
        low = re.sub(r"\s+", " ", low)
        toks = set(tokenize(text))
        for f in cfg.followups:
            given = bool(f.named_tokens and toks & f.named_tokens) or bool(f.named_patterns and any_match(f.named_patterns, low))
            self.named[f.field] = self.named.get(f.field, False) or given

        # 0. pre-call policy, first turn only
        if cfg.precheck and not self.prev_caller:
            r = cfg.precheck(self.context)
            if r:
                return Decision(*r)

        # 1. must-escalate rules
        hits = cfg.matcher.match(text)
        if hits:
            for level in cfg.level_priority:
                h = next((h for h in hits if h.level == level), None)
                if h:
                    action, reply, fmt = cfg.level_actions[level]
                    return Decision(action, reply, fmt.format(cat=h.category, a=h.a, b=h.b))

        # 2. pattern stages (human request etc.)
        for st in cfg.stages:
            if any_match(st.patterns, low):
                return Decision(st.action, st.reply, st.name)

        # 3. optional LLM classifier (only when the rules found nothing)
        if self.use_llm and cfg.llm_system:
            d = self._llm_check(text)
            if d is not None:
                return d

        # 4. failed captures
        failed = False
        if last_agent and any_match(cfg.clarify_patterns, last_agent):
            failed = True
        if any_match(cfg.correction_patterns, low):
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
            if self.failed_captures >= cfg.fail_limit:
                return Decision(cfg.transfer_action, cfg.reply_transfer_fails, f"{self.failed_captures} failed captures")

        # 5. follow-up completeness note for the agent
        for f in cfg.followups:
            if any_match(f.trigger_patterns, low) and not self.named.get(f.field):
                return Decision(None, None, f"{f.field} missing", note=f.note)
        return Decision(None, None, "pass")

    def _llm_check(self, text: str) -> Decision | None:
        r = llm.generate(f"Caller utterance: {text}", system=self.cfg.llm_system, model=self.cfg.llm_model, temperature=0.0)
        self.llm_latency_s += r["latency_s"]
        try:
            j = llm.parse_json(r["text"])
        except Exception:  # noqa: BLE001
            return None
        if isinstance(j, list):
            j = j[0] if j else {}
        for key, (action, reply, reason) in self.cfg.llm_labels.items():
            if j.get(key):
                return Decision(action, reply, reason)
        return None
