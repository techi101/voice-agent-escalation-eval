"""Domain 1: UK GP clinic phone line (AI receptionist).

Every domain package exposes the same names, used by the shared harness in vaeval/:
  NAME, TITLE, SLICES, build_scenarios()              -> the spec (ground truth)
  WRITER_SYSTEM, CHECKER_SYSTEM, accept(), WRITER_MODEL -> transcript writing and checking
  CONFUSIONS, NAMES_TO_MANGLE                         -> ASR noise word lists
  agent_system(row), AGENT_ACTIONS, TERMINAL, NOTE_TEMPLATE, AGENT_MODEL -> baseline agent
  GUARD_CONFIG, guard_context(row)                    -> guard layer
  ASK_PATTERNS                                        -> follow-up detector
  ROUTINE, TRANSFER, ESCALATIONS, METRICS             -> scoring
"""
from vaeval.llm import DEFAULT_MODEL

from .agent_prompt import AGENT_ACTIONS, TERMINAL, agent_system  # noqa: F401
from .followup_patterns import ASK_PATTERNS  # noqa: F401
from .guard_config import CONFIG as GUARD_CONFIG  # noqa: F401
from .noise import CONFUSIONS, NAMES_TO_MANGLE  # noqa: F401
from .spec import ADVISE_111, ADVISE_999, ROUTINE, SLICES, TRANSFER, build_scenarios  # noqa: F401
from .writer import CHECKER_SYSTEM, WRITER_SYSTEM, accept  # noqa: F401

NAME = "gp_clinic"
TITLE = "UK GP clinic phone line"
WRITER_MODEL = DEFAULT_MODEL      # gemini-3.5-flash-lite
AGENT_MODEL = DEFAULT_MODEL       # gemini-3.5-flash-lite
NOTE_TEMPLATE = "{text}\n\n[Call-checking layer note to the receptionist: {note}]"
ESCALATIONS = {ADVISE_999, ADVISE_111}


def guard_context(row: dict) -> dict:
    return {}


# (key, label, how it is computed, which scenario groups)
METRICS = [
    ("red_flag_recall", "Red-flag escalation recall", "correct", ["red_flag"]),
    ("human_handoff_recall", "Human handoff recall", "transfer", ["human", "capture"]),
    ("handoff_within_policy", "Handoff within policy turn", "transfer_in_time", ["human", "capture"]),
    ("false_escalation_hard_neg", "False escalation (hard negatives)", "escalated", ["hard_negative"]),
    ("unneeded_transfer_routine", "Unneeded transfer (routine + hard neg)", "transfer", ["routine", "hard_negative"]),
    ("followup_completeness", "Follow-up completeness", "followup", None),
]
