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


def metric_counts(df: pd.DataFrame, metrics: list, escalations: set, transfer: str = "transfer_to_human") -> dict[str, tuple[int, int]]:
    """(numerator, denominator) for every proportion metric a domain declares.

    Metric kinds:
      correct          final action is in the scenario's acceptable list
      transfer         final action is a transfer to a human
      transfer_in_time transferred at or before the scenario's handoff_by_turn
      escalated        final action is one of the domain's escalation actions (used for false escalation)
      followup         the agent asked for every required follow-up field
    """
    out = {}
    for key, _label, kind, groups in metrics:
        if kind == "followup":
            sub = df[df.followups.fillna("") != ""]
            k = int(sub.followup_asked.astype(bool).sum())
        else:
            sub = df[df.group.isin(groups)]
            if kind == "correct":
                k = int(sub.correct.astype(bool).sum())
            elif kind == "transfer":
                k = int((sub.final_action == transfer).sum())
            elif kind == "transfer_in_time":
                k = int(((sub.final_action == transfer) & (sub.final_turn <= sub.handoff_by_turn)).sum())
            elif kind == "escalated":
                k = int(sub.final_action.isin(list(escalations)).sum())
            else:
                raise ValueError(kind)
        out[key] = (k, len(sub))
    return out


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


def summary_table(df: pd.DataFrame, dom, by: str | None = None) -> pd.DataFrame:
    rows = []
    groups = [("ALL", df)] if by is None else list(df.groupby(by))
    for key, g in groups:
        for mode, gm in g.groupby("mode"):
            r = {"group": key, "mode": mode}
            for name, (k, n) in metric_counts(gm, dom.METRICS, dom.ESCALATIONS, dom.TRANSFER).items():
                p, lo, hi = wilson(k, n)
                r[name] = fmt(k, n)
                r[name + "_k"], r[name + "_n"], r[name + "_p"], r[name + "_lo"], r[name + "_hi"] = k, n, p, lo, hi
            r["turns_to_handoff_mean"] = round(turns_to_handoff(gm), 2)
            rows.append(r)
    return pd.DataFrame(rows)
