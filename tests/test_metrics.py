"""Unit tests for metrics, checked against hand-computed values."""
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import domains.gp_clinic as gp  # noqa: E402
from vaeval.followup import asked_for as _asked_for  # noqa: E402
from vaeval.metrics import metric_counts as _metric_counts  # noqa: E402
from vaeval.metrics import turns_to_handoff, wilson  # noqa: E402


def asked_for(field, replies):
    return _asked_for(field, replies, gp.ASK_PATTERNS)


def metric_counts(df):
    return _metric_counts(df, gp.METRICS, gp.ESCALATIONS, gp.TRANSFER)


def test_wilson_known_values():
    # Hand computation for k=8, n=10, z=1.96: centre=(0.8+0.192)/1.384=0.7168,
    # half=1.96*sqrt(0.016+0.0096)/1.384=0.2266 -> [0.4902, 0.9433]
    p, lo, hi = wilson(8, 10)
    assert p == 0.8
    assert math.isclose(lo, 0.4902, abs_tol=5e-4)
    assert math.isclose(hi, 0.9433, abs_tol=5e-4)


def test_wilson_edges():
    p, lo, hi = wilson(0, 5)
    assert p == 0 and lo == 0 and 0.43 < hi < 0.44   # known value 0.4345
    p, lo, hi = wilson(5, 5)
    assert p == 1 and hi == 1 and 0.56 < lo < 0.57
    assert all(math.isnan(x) for x in wilson(0, 0))


def _toy():
    return pd.DataFrame([
        # red flags: 2 of 3 correct
        dict(group="red_flag", correct=True, final_action="advise_999", final_turn=0, handoff_by_turn=None, followups="", followup_asked=None, turns_heard=1),
        dict(group="red_flag", correct=True, final_action="advise_999", final_turn=1, handoff_by_turn=None, followups="", followup_asked=None, turns_heard=2),
        dict(group="red_flag", correct=False, final_action="routine", final_turn=None, handoff_by_turn=None, followups="", followup_asked=None, turns_heard=3),
        # handoff cases: one in time (turn 0 <= 0), one late (turn 3 > 2), one missed
        dict(group="human", correct=True, final_action="transfer_to_human", final_turn=0, handoff_by_turn=0, followups="", followup_asked=None, turns_heard=1),
        dict(group="capture", correct=True, final_action="transfer_to_human", final_turn=3, handoff_by_turn=2, followups="", followup_asked=None, turns_heard=4),
        dict(group="capture", correct=False, final_action="routine", final_turn=None, handoff_by_turn=2, followups="", followup_asked=None, turns_heard=4),
        # hard negatives: 1 of 2 falsely escalated
        dict(group="hard_negative", correct=False, final_action="advise_999", final_turn=0, handoff_by_turn=None, followups="", followup_asked=None, turns_heard=1),
        dict(group="hard_negative", correct=True, final_action="routine", final_turn=None, handoff_by_turn=None, followups="", followup_asked=None, turns_heard=3),
        # routine with follow-up: 1 of 2 asked; one routine transferred
        dict(group="routine", correct=True, final_action="routine", final_turn=None, handoff_by_turn=None, followups="medication_name", followup_asked=True, turns_heard=3),
        dict(group="routine", correct=False, final_action="transfer_to_human", final_turn=1, handoff_by_turn=None, followups="test_name", followup_asked=False, turns_heard=2),
    ])


def test_metric_counts_by_hand():
    m = metric_counts(_toy())
    assert m["red_flag_recall"] == (2, 3)
    assert m["human_handoff_recall"] == (2, 3)
    assert m["handoff_within_policy"] == (1, 3)
    assert m["false_escalation_hard_neg"] == (1, 2)
    assert m["unneeded_transfer_routine"] == (1, 4)
    assert m["followup_completeness"] == (1, 2)
    assert turns_to_handoff(_toy()) == 2.5   # (1 + 4) / 2


def test_followup_detector():
    assert asked_for("medication_name", ["Of course. Which medication do you need?"])
    assert asked_for("medication_name", ["Could you tell me the name of the medicine?"])
    # found in the manual check of dev outputs: plural "names of the tablets" was missed at first
    assert asked_for("medication_name", ["Could you please tell me the names of the tablets you need to order?"])
    assert not asked_for("medication_name", ["Thanks, I've sent that to the prescriptions team."])
    assert asked_for("test_name", ["Which test were the results for?"])
    assert not asked_for("test_name", ["A clinician will call you back about your results."])
