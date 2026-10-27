"""List every case the guarded system still gets wrong, with the full call.

Usage: python scripts/error_analysis.py --domain gp_clinic --split test --mode guard
Writes results/<domain>/<split>/errors_<mode>.md
"""
import argparse
import json
from pathlib import Path

import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaeval import domain  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=domain.DOMAINS)
    ap.add_argument("--split", default="test")
    ap.add_argument("--mode", default="guard")
    args = ap.parse_args()
    res = domain.results_dir(args.domain, args.split)
    d = pd.read_csv(res / f"calls_{args.mode}.csv")
    base = pd.read_csv(res / "calls_baseline.csv").set_index("id")
    late = d.group.isin(["human", "capture"]) & (d.final_action == "transfer_to_human") & (d.final_turn > d.handoff_by_turn)
    fu_miss = (d.followups.fillna("") != "") & (d.followup_asked.astype(str) == "False")
    bad = d[(~d.correct) | late | fu_miss]
    out = [f"# Remaining errors: {args.domain}, {args.mode}, {args.split} split ({len(bad)} of {len(d)} calls)\n",
           "Each entry: what was expected, what happened, what the baseline did, then the call turn by turn.\n"]
    for kind, sub in [("Wrong outcome", d[~d.correct]), ("Correct but late handoff", d[late & d.correct]),
                      ("Missing follow-up question", d[fu_miss & d.correct])]:
        out.append(f"\n## {kind} ({len(sub)})\n")
        for _, r in sub.iterrows():
            b = base.loc[r.id]
            out.append(f"\n### {r.id}\nexpected `{r.expected}`; got `{r.final_action}` at caller turn {r.final_turn} "
                       f"(decided by {r.decided_by}; guard reason: {r.guard_reason}); baseline got `{b.final_action}`.\n")
            for t in json.loads(r.log):
                out.append(f"- caller: {t['caller'].splitlines()[0]}\n  - guard: {t['guard']}; agent/guard reply: {t['reply']} -> `{t['action']}`\n")
    path = res / f"errors_{args.mode}.md"
    path.write_text("".join(out), encoding="utf-8")
    print(f"wrote {path} ({len(bad)} cases)")


if __name__ == "__main__":
    main()
