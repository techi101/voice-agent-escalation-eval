"""Follow-up completeness checker (rule-based).

A request is "complete" if the information staff need is either given by the
caller or asked for by the agent before the call ends. Example from public
reporting (Gordon House, May 2026): a patient said they needed medication and
was not asked which one, so staff had to call back.

Required fields per request kind live in scenarios.ROUTINE_KINDS. Here we only
detect whether the agent ASKED for a missing field. The detector is a regex,
checked by hand on a sample (see results/spot_check.md).
"""
from __future__ import annotations

import re

ASK_PATTERNS = {
    "medication_name": [
        r"\b(which|what)\b[^.?]{0,40}\b(medicine|medicines|medication|medications|tablets|prescription|item|items|drug|drugs|inhaler)\b",
        r"\bname of\b[^.?]{0,30}\b(medicine|medication|tablets|drug)\b",
        r"\b(medicine|medication)s?\b[^.?]{0,30}\b(called|name)\b",
        r"\bwhat (is it|do you need|are you after)\b",
    ],
    "test_name": [
        r"\b(which|what)\b[^.?]{0,40}\b(test|tests|results? (is|are|was|were) (it|they|for)|blood test|scan|investigation)\b",
        r"\bwhat (kind|type) of\b[^.?]{0,20}\b(test|results?)\b",
        r"\bwhat\b[^.?]{0,20}\bresults?\b[^.?]{0,20}\bfor\b",
    ],
}


def asked_for(field: str, agent_replies: list[str]) -> bool:
    pats = ASK_PATTERNS[field]
    return any(re.search(p, r, flags=re.I) for r in agent_replies for p in pats)
