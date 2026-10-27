"""Independent recomputation of the headline numbers for one domain.

Reads results/<domain>/<split>/calls_*.csv with the csv module only (no pandas,
no vaeval.metrics), recomputes each proportion and its Wilson interval from
scratch, and compares with summary_overall.csv. It also re-derives "correct"
from the scenario spec (data/<domain>/scenarios.jsonl) rather than trusting
the column written by the runner.

Usage: python scripts/sanity_check.py --domain gp_clinic --split test
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaeval import domain  # noqa: E402  (only used for the metric list and paths)


def wilson_again(k, n):
    # written out separately on purpose (different form from vaeval.metrics)
    z = 1.96
    phat = k / n
    a = phat + z * z / (2 * n)
    b = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    c = 1 + z * z / n
    return phat, (a - b) / c, (a + b) / c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=domain.DOMAINS)
    ap.add_argument("--split", default="test")
    args = ap.parse_args()
    dom = domain.load(args.domain)
    out = domain.results_dir(args.domain, args.split)
    spec = {}
    for line in (domain.data_dir(args.domain) / "scenarios.jsonl").open(encoding="utf-8"):
        s = json.loads(line)
        spec[s["id"]] = s
    summary = {r["mode"]: r for r in csv.DictReader((out / "summary_overall.csv").open(encoding="utf-8"))}
    problems = 0
    for path in sorted(out.glob("calls_*.csv")):
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        mode = rows[0]["mode"]
        print(f"[{args.domain} / {mode}] {len(rows)} calls")
        for key, _label, kind, groups in dom.METRICS:
            k = n = 0
            for r in rows:
                s = spec[r["id"]]
                correct = r["final_action"] in s["acceptable"]       # from the spec, not the csv column
                if str(correct) != r["correct"]:
                    print(f"  MISMATCH correct column for {r['id']}")
                    problems += 1
                if kind == "followup":
                    if s["followups"]:
                        n += 1
                        k += r["followup_asked"] == "True"
                    continue
                if s["group"] not in groups:
                    continue
                n += 1
                if kind == "correct":
                    k += correct
                elif kind == "transfer":
                    k += r["final_action"] == dom.TRANSFER
                elif kind == "transfer_in_time":
                    k += r["final_action"] == dom.TRANSFER and float(r["final_turn"]) <= float(s["handoff_by_turn"])
                elif kind == "escalated":
                    k += r["final_action"] in dom.ESCALATIONS
            if n == 0:
                continue
            p, lo, hi = wilson_again(k, n)
            sk, sn = int(summary[mode][key + "_k"]), int(summary[mode][key + "_n"])
            slo, shi = float(summary[mode][key + "_lo"]), float(summary[mode][key + "_hi"])
            ok = (k, n) == (sk, sn) and abs(lo - slo) < 1e-3 and abs(hi - shi) < 1e-3
            problems += not ok
            print(f"  {key:30s} recomputed {k}/{n}={p:.3f} [{lo:.3f},{hi:.3f}]  summary {sk}/{sn} [{slo:.3f},{shi:.3f}]  {'OK' if ok else 'MISMATCH'}")
    print("SANITY CHECK", "PASSED" if problems == 0 else f"FAILED ({problems} problems)")


if __name__ == "__main__":
    main()
