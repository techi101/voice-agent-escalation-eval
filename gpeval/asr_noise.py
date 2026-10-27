"""Deterministic speech-to-text (ASR) noise injector.

Takes clean caller text and makes it look like a noisy phone-line transcript:
  * substitutions from a small confusion list of sound-alike words
    (e.g. "peter" -> "pizza", "chest" -> "chess", "breathe" -> "breed")
  * dropped words
  * "[inaudible]" gaps
The random generator is seeded by the scenario id, so the same input always
gives the same noisy output. The target word error rate (WER) is approximate.
"""
from __future__ import annotations

import random
import re

CONFUSIONS = {
    "peter": "pizza", "claire": "clear", "tom": "tim", "johnson": "johnston", "bennett": "bonnet",
    "ashworth": "ash worth", "chest": "chess", "pain": "pane", "breathe": "breed", "breathing": "breeding",
    "breath": "bread", "stroke": "stroll", "face": "phase", "arm": "harm", "speech": "peach",
    "speak": "sneak", "words": "worlds", "slurred": "slid", "tablets": "tablet", "prescription": "subscription",
    "appointment": "a point meant", "swelling": "smelling", "throat": "throw", "results": "resorts",
    "tongue": "tong", "numb": "num", "weak": "week", "rash": "rush", "confused": "confuse",
    "dizzy": "busy", "lips": "lisp", "blue": "blew", "tight": "tide", "heart": "hard", "sick": "sik",
    "repeat": "receipt", "doctor": "doctors", "blood": "bud", "pressure": "pleasure", "wheezing": "wheeling",
    "swallow": "swallowed", "drooping": "dropping", "suddenly": "sudden", "collapsed": "collapse",
}

_WORD = re.compile(r"[A-Za-z']+|[^A-Za-z'\s]+")


def add_noise(text: str, wer: float, seed: str) -> str:
    """Return a noisy copy of `text` with roughly `wer` of words corrupted."""
    if wer <= 0:
        return text
    rng = random.Random(seed)
    out = []
    for tok in text.split():
        core = re.sub(r"[^A-Za-z']", "", tok).lower()
        if core and rng.random() < wer:
            if core in CONFUSIONS:
                out.append(CONFUSIONS[core])
            else:
                r = rng.random()
                if r < 0.6:
                    continue  # word dropped
                out.append("[inaudible]")
        else:
            out.append(tok)
    return " ".join(out)


def mangle_names(text: str, seed: str, p: float = 0.8) -> str:
    """Mangle known first names / surnames (e.g. Peter -> Pizza) with probability p."""
    rng = random.Random(seed + "-names")
    words = text.split()
    for i, w in enumerate(words):
        core = re.sub(r"[^A-Za-z']", "", w).lower()
        if core in ("peter", "claire", "tom", "johnson", "bennett", "ashworth") and rng.random() < p:
            words[i] = CONFUSIONS[core]
    return " ".join(words)
