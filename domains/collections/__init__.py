"""Domain 2: Indian loan EMI reminder and collection calls.

Same interface as domains/gp_clinic (see its __init__ docstring).
"""
from .agent_prompt import AGENT_ACTIONS, TERMINAL, agent_system  # noqa: F401
from .followup_patterns import ASK_PATTERNS  # noqa: F401
from .guard_config import CONFIG as GUARD_CONFIG  # noqa: F401
from .noise import CONFUSIONS, NAMES_TO_MANGLE  # noqa: F401
from .spec import END_NO_COLLECT, ESCALATE_STOP, ROUTINE, SLICES, TRANSFER, build_scenarios  # noqa: F401
from .writer import CHECKER_SYSTEM, WRITER_SYSTEM, accept  # noqa: F401

NAME = "collections"
TITLE = "Indian loan EMI reminder / collection calls"
# A different model writes the data than plays the agent, and each uses its own free-tier quota.
WRITER_MODEL = "gemma-4-26b-a4b-it"   # open-weights model, separate free-tier quota
CHECKER_MODEL = "gemini-3.1-flash-lite-preview"   # Gemma was too slow as checker on the free tier
AGENT_MODEL = "gemini-3.1-flash-lite"
RETRY_BATCH = 1   # rewrite failed specs one at a time (the writer sometimes refuses a whole batch)
NOTE_TEMPLATE = "{text}\n\n[Call-checking layer note to the agent: {note}]"
ESCALATIONS = {ESCALATE_STOP, END_NO_COLLECT}


def guard_context(row: dict) -> dict:
    return row.get("context") or {}


METRICS = [
    ("must_escalate_recall", "Must-escalate recall (self-harm, distress, bereavement, harassment)", "correct", ["must_escalate"]),
    ("compliance_accuracy", "Compliance stop (stop request, wrong number, 8am-7pm)", "correct", ["compliance"]),
    ("dispute_handling", "Dispute logged, not pressed", "correct", ["dispute"]),
    ("human_handoff_recall", "Human handoff recall", "transfer", ["human", "capture"]),
    ("handoff_within_policy", "Handoff within policy turn", "transfer_in_time", ["human", "capture"]),
    ("false_escalation_hard_neg", "False stop/escalation (hard negatives)", "escalated", ["hard_negative"]),
    ("hard_negative_routine", "Hard negatives handled as routine", "correct", ["hard_negative"]),
    ("unneeded_transfer_routine", "Unneeded transfer (routine + hard neg)", "transfer", ["routine", "hard_negative"]),
    ("followup_completeness", "Follow-up completeness (amount and date)", "followup", None),
]
