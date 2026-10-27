"""The Scenario record shared by all domains, and the dev/test splitter.

A Scenario is one test case written in code. Its `expected` and `acceptable`
fields are the ground truth. An LLM later writes only the caller's words.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field


@dataclass
class Scenario:
    id: str
    slice: str
    group: str          # domain-defined, e.g. red_flag | routine | hard_negative | human | capture
    kind: str           # e.g. stroke_face, rx_unnamed, human, capture
    expected: str       # expected final action
    acceptable: list    # actions that count as correct
    brief: str          # plain-English content brief for the writer
    persona: str
    persona_note: str
    n_turns: int
    signal_turn: int | None     # 0-based caller turn where the key signal first appears
    turn_plan: list = field(default_factory=list)
    followups: list = field(default_factory=list)   # required follow-up fields
    handoff_by_turn: int | None = None              # policy deadline for human handoff (0-based caller turn)
    asr_wer: float = 0.0
    source: str = ""
    split: str = ""
    context: dict = field(default_factory=dict)     # domain extras (e.g. call time, EMI amount)

    def to_dict(self):
        return asdict(self)


def assign_splits(scenarios: list[Scenario], dev_frac: float = 0.4) -> None:
    """Deterministic 40/60 dev/test split by scenario, stratified by slice x group.

    Within each (slice, group) cell, scenarios are ordered by a hash of their id
    and the first round(dev_frac * n) go to dev. The split is fixed before any
    guard is written, and guards are tuned on dev only.
    """
    cells: dict[tuple, list[Scenario]] = {}
    for s in scenarios:
        cells.setdefault((s.slice, s.group), []).append(s)
    for cell in cells.values():
        cell.sort(key=lambda s: hashlib.sha256(s.id.encode()).hexdigest())
        n_dev = round(dev_frac * len(cell))
        for i, s in enumerate(cell):
            s.split = "dev" if i < n_dev else "test"
