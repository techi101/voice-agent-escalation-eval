"""Deterministic speech-to-text (ASR) noise injector, shared by all domains.

Takes clean caller text and makes it look like a noisy phone-line transcript:
  * substitutions from a domain's confusion list of sound-alike words
    (e.g. GP: "peter" -> "pizza", "chest" -> "chess"; collections: "emi" -> "amy")
  * dropped words
  * "[inaudible]" gaps
The random generator is seeded by the scenario id, so the same input always
gives the same noisy output. The target word error rate (WER) is approximate.
"""
from __future__ import annotations

import random
import re


def add_noise(text: str, wer: float, seed: str, confusions: dict) -> str:
    """Return a noisy copy of `text` with roughly `wer` of words corrupted."""
    if wer <= 0:
        return text
    rng = random.Random(seed)
    out = []
    for tok in text.split():
        core = re.sub(r"[^A-Za-z']", "", tok).lower()
        if core and rng.random() < wer:
            if core in confusions:
                out.append(confusions[core])
            else:
                r = rng.random()
                if r < 0.6:
                    continue  # word dropped
                out.append("[inaudible]")
        else:
            out.append(tok)
    return " ".join(out)


def mangle_names(text: str, seed: str, names: tuple, confusions: dict, p: float = 0.8) -> str:
    """Mangle known names (e.g. Peter -> Pizza) with probability p, using the confusion list."""
    rng = random.Random(seed + "-names")
    words = text.split()
    for i, w in enumerate(words):
        core = re.sub(r"[^A-Za-z']", "", w).lower()
        if core in names and rng.random() < p:
            words[i] = confusions[core]
    return " ".join(words)
