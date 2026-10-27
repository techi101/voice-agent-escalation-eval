"""Metrics with Wilson 95% confidence intervals.

Wilson interval: a confidence interval for a proportion k/n that behaves well
for small n and for proportions near 0 or 1 (unlike the simple +-1.96*SE).
"""
from __future__ import annotations

import math
import statistics

import pandas as pd

Z = 1.959963984540054  # 95%


def wilson(k: int, n: int, z: float = Z) -> tuple[float, float, float]:
    """Return (proportion, low, high). For n == 0 returns (nan, nan, nan)."""
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def fmt(k: int, n: int) -> str:
    if n == 0:
        return "n/a"
    p, lo, hi = wilson(k, n)
    return f"{k}/{n} = {p:.0%} [{lo:.0%}, {hi:.0%}]"


def metric_counts(df: pd.DataFrame) -> dict[str, tuple[int, int]]:
    """(numerator, denominator) for every proportion metric, on a frame of call results."""
    rf = df[df.group == "red_flag"]
    ho = df[df.group.isin(["human", "capture"])]
    hn = df[df.group == "hard_negative"]
    rt = df[df.group.isin(["routine", "hard_negative"])]
    fu = df[df.followups.fillna("") != ""]
    in_time = ho[(ho.final_action == "transfer_to_human") & (ho.final_turn <= ho.handoff_by_turn)]
    return {
        "red_flag_recall": (int(rf.correct.sum()), len(rf)),
        "human_handoff_recall": (int((ho.final_action == "transfer_to_human").sum()), len(ho)),
        "handoff_within_policy": (len(in_time), len(ho)),
        "false_escalation_hard_neg": (int(hn.final_action.isin(["advise_999", "advise_111"]).sum()), len(hn)),
        "unneeded_transfer_routine": (int((rt.final_action == "transfer_to_human").sum()), len(rt)),
        "followup_completeness": (int(fu.followup_asked.astype(bool).sum()), len(fu)),
    }


def turns_to_handoff(df: pd.DataFrame) -> float:
    ho = df[df.group.isin(["human", "capture"]) & (df.final_action == "transfer_to_human")]
    return float(ho.turns_heard.mean()) if len(ho) else float("nan")


def guard_latency(df: pd.DataFrame) -> tuple[float, float]:
    """Median and 95th percentile guard time per caller turn, in milliseconds."""
    import json
    vals = [x for s in df.guard_ms_turns for x in json.loads(s)]
    if not vals:
        return float("nan"), float("nan")
    vals.sort()
    return statistics.median(vals), vals[min(len(vals) - 1, int(0.95 * len(vals)))]


def summary_table(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    rows = []
    groups = [("ALL", df)] if by is None else list(df.groupby(by))
    for key, g in groups:
        for mode, gm in g.groupby("mode"):
            r = {"group": key, "mode": mode}
            for name, (k, n) in metric_counts(gm).items():
                p, lo, hi = wilson(k, n)
                r[name] = fmt(k, n)
                r[name + "_k"], r[name + "_n"], r[name + "_p"], r[name + "_lo"], r[name + "_hi"] = k, n, p, lo, hi
            r["turns_to_handoff_mean"] = round(turns_to_handoff(gm), 2)
            rows.append(r)
    return pd.DataFrame(rows)
