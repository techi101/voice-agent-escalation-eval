"""Independent recomputation of the headline numbers.

Reads results/<split>/calls_*.csv with the csv module only (no pandas, no
gpeval.metrics), recomputes each proportion and its Wilson interval from
scratch, and compares with results/<split>/summary_overall.csv. Also
re-derives "correct" from the scenario spec (data/scenarios.jsonl) rather than
trusting the column written by the runner.

Usage: python scripts/sanity_check.py --split test
"""
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def wilson_again(k, n):
    # written out separately on purpose (different form from gpeval.metrics)
    if n == 0:
        return None
    z = 1.96
    phat = k / n
    a = phat + z * z / (2 * n)
    b = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    c = 1 + z * z / n
    return phat, (a - b) / c, (a + b) / c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    args = ap.parse_args()
    out = ROOT / "results" / args.split
    spec = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data" / "scenarios.jsonl").open(encoding="utf-8")}
    summary = {r["mode"]: r for r in csv.DictReader((out / "summary_overall.csv").open(encoding="utf-8"))}
    problems = 0
    for path in sorted(out.glob("calls_*.csv")):
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        mode = rows[0]["mode"]
        counts = {k: [0, 0] for k in ["red_flag_recall", "human_handoff_recall", "false_escalation_hard_neg", "followup_completeness"]}
        for r in rows:
            s = spec[r["id"]]
            correct = r["final_action"] in s["acceptable"]          # from the spec, not the csv column
            if str(correct) != r["correct"]:
                print(f"  MISMATCH correct column for {r['id']}")
                problems += 1
            if s["group"] == "red_flag":
                counts["red_flag_recall"][1] += 1
                counts["red_flag_recall"][0] += correct
            if s["group"] in ("human", "capture"):
                counts["human_handoff_recall"][1] += 1
                counts["human_handoff_recall"][0] += r["final_action"] == "transfer_to_human"
            if s["group"] == "hard_negative":
                counts["false_escalation_hard_neg"][1] += 1
                counts["false_escalation_hard_neg"][0] += r["final_action"] in ("advise_999", "advise_111")
            if s["followups"]:
                counts["followup_completeness"][1] += 1
                counts["followup_completeness"][0] += r["followup_asked"] == "True"
        print(f"[{mode}] {len(rows)} calls")
        for name, (k, n) in counts.items():
            p, lo, hi = wilson_again(k, n)
            sk, sn = int(summary[mode][name + "_k"]), int(summary[mode][name + "_n"])
            slo, shi = float(summary[mode][name + "_lo"]), float(summary[mode][name + "_hi"])
            ok = (k, n) == (sk, sn) and abs(lo - slo) < 1e-3 and abs(hi - shi) < 1e-3
            problems += not ok
            print(f"  {name:28s} recomputed {k}/{n}={p:.3f} [{lo:.3f},{hi:.3f}]  summary {sk}/{sn} [{slo:.3f},{shi:.3f}]  {'OK' if ok else 'MISMATCH'}")
    print("SANITY CHECK", "PASSED" if problems == 0 else f"FAILED ({problems} problems)")


if __name__ == "__main__":
    main()
