"""Shared rule matcher used by every domain's guard.

How it works, in plain terms:
  1. Clean the text: lowercase, keep letters/numbers/apostrophes only.
  2. Each rule is a PAIR of word lists, A and B. The rule fires when a word
     from A and a word from B appear within `window` words of each other.
     Example (GP): A = {chest, chhati, seene}, B = {pain, dard, tight, crushing}.
  3. Words are compared with fuzzy matching (rapidfuzz ratio), so small ASR
     spelling errors still match ("breething" ~ "breathing").
  4. A hit is ignored if the words around it talk about the past
     ("last year", "since my stroke two years ago") and nothing around it says
     it is happening now ("suddenly", "this morning", "right now").
The word lists (RULES, PAST, NOW) live in each domain folder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

_CLEAN = re.compile(r"[^a-z0-9'\s]")


_NOT_NEW = re.compile(r"\b(nothing|nowt|no|not|nae|nothin)\s+(\w+\s+)?new\b")


def tokenize(text: str) -> list[str]:
    t = text.lower().replace("’", "'")
    t = re.sub(r"'s\b", "", t)          # "arm's" -> "arm"
    t = _NOT_NEW.sub(" notnew ", t)        # "nothing new" is a past/stable marker, not a "now" marker
    return _CLEAN.sub(" ", t).split()


def word_in(tok: str, vocab: set, thresh: int = 85) -> bool:
    if tok in vocab:
        return True
    if len(tok) < 5:          # short words: exact only (avoid "arm" ~ "farm" style noise)
        return False
    return any(len(v) >= 5 and fuzz.ratio(tok, v) >= thresh for v in vocab)


@dataclass
class Hit:
    category: str
    level: str
    a: str
    b: str
    position: int


def find_hits(text: str, rules_by_cat: dict) -> list[Hit]:
    toks = tokenize(text)
    hits: list[Hit] = []
    for cat, (level, rules) in rules_by_cat.items():
        for A, B, window in rules:
            a_pos = [i for i, t in enumerate(toks) if word_in(t, A)]
            if not a_pos:
                continue
            b_pos = [i for i, t in enumerate(toks) if word_in(t, B)]
            for i in a_pos:
                js = [j for j in b_pos if j != i and abs(j - i) <= window]
                if js:
                    hits.append(Hit(cat, level, toks[i], toks[js[0]], i))
                    break
            if hits and hits[-1].category == cat:
                break
    return hits


def is_historical(text: str, pos: int, past: set, now: set, span: int = 12) -> bool:
    """True if words near position `pos` describe the past and nothing nearby says 'now'."""
    toks = tokenize(text)
    lo = max(0, pos - span)
    near = toks[lo: pos + span + 1]
    past_found = False
    for k, t in enumerate(near):
        if t in past:
            # "since this morning" / "since i woke up today" is about now, not the past
            if t == "since" and any(x in now for x in toks[lo + k + 1: lo + k + 5]):
                continue
            past_found = True
    return past_found and not any(t in now for t in near)


@dataclass
class Matcher:
    """A domain's rule set: RULES {category: (level, [(A, B, window), ...])}, PAST and NOW word sets."""
    rules: dict
    past: set
    now: set
    span: int = 12

    def match(self, text: str) -> list[Hit]:
        """Hits in `text` that are not about the past."""
        return [h for h in find_hits(text, self.rules)
                if not is_historical(text, h.position, self.past, self.now, self.span)]
