"""Follow-up completeness checker (rule-based), shared by all domains.

A request is "complete" if the information staff need is either given by the
caller or asked for by the agent before the call ends. Example from public
reporting (Gordon House GP surgery, May 2026): a patient said they needed
medication and was not asked which one, so staff had to call back.

Required fields per request kind live in each domain's spec. Here we only
detect whether the agent ASKED for a missing field, using the domain's regexes
(domains/<name>/followup_patterns.py), checked by hand on a sample.
"""
from __future__ import annotations

import re


def asked_for(field: str, agent_replies: list[str], ask_patterns: dict) -> bool:
    pats = ask_patterns[field]
    return any(re.search(p, r, flags=re.I) for r in agent_replies for p in pats)
