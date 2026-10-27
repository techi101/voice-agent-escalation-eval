"""Run the evaluation and write results.

Usage:
  python scripts/run_eval.py --split dev                 # for tuning the guard
  python scripts/run_eval.py --split test                # headline numbers
  python scripts/run_eval.py --split test --modes baseline guard guard_llm
Outputs go to results/<split>/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gpeval import llm  # noqa: E402
from gpeval.metrics import guard_latency, summary_table  # noqa: E402
from gpeval.runner import run_all  # noqa: E402

COLS = ["red_flag_recall", "human_handoff_recall", "handoff_within_policy", "false_escalation_hard_neg",
        "unneeded_transfer_routine", "followup_completeness", "turns_to_handoff_mean"]
NAMES = {"red_flag_recall": "Red-flag escalation recall", "human_handoff_recall": "Human handoff recall",
         "handoff_within_policy": "Handoff within policy turn", "false_escalation_hard_neg": "False escalation (hard negatives)",
         "unneeded_transfer_routine": "Unneeded transfer (routine + hard neg)", "followup_completeness": "Follow-up completeness",
         "turns_to_handoff_mean": "Mean caller turns until handoff"}


def to_markdown(df: pd.DataFrame, cols) -> str:
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n" for _, r in df.iterrows())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["dev", "test", "all"])
    ap.add_argument("--modes", nargs="+", default=["baseline", "guard"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    rows = [json.loads(line) for line in (ROOT / "data" / "transcripts.jsonl").open(encoding="utf-8")]
    if args.split != "all":
        rows = [r for r in rows if r["split"] == args.split]
    out = ROOT / "results" / args.split
    out.mkdir(parents=True, exist_ok=True)

    frames = []
    for mode in args.modes:
        t0 = time.time()
        res = run_all(rows, mode, workers=args.workers)
        df = pd.DataFrame(res)
        df.to_csv(out / f"calls_{mode}.csv", index=False, encoding="utf-8")
        frames.append(df)
        print(f"{mode}: {len(df)} calls in {time.time() - t0:.0f}s; LLM {llm.STATS}", flush=True)
    df = pd.concat(frames)

    overall = summary_table(df)
    by_slice = summary_table(df, by="slice")
    overall.to_csv(out / "summary_overall.csv", index=False)
    by_slice.to_csv(out / "summary_by_slice.csv", index=False)

    md = [f"# Results: {args.split} split ({len(rows)} scenarios)\n",
          "Cells: k/n = rate [Wilson 95% interval]. Higher is better except false escalation, unneeded transfer and turns.\n",
          "## Overall\n"]
    t = overall.copy()
    md.append(to_markdown(t.rename(columns=NAMES), ["mode"] + [NAMES[c] for c in COLS]))
    for metric in COLS[:-1]:
        md.append(f"\n## {NAMES[metric]} by slice\n")
        piv = by_slice.pivot(index="group", columns="mode", values=metric).reset_index()
        md.append(to_markdown(piv, list(piv.columns)))
    lat = []
    for mode, g in df.groupby("mode"):
        med, p95 = guard_latency(g)
        calls = g.n_agent_calls.sum()
        n_turns = sum(len(json.loads(x)) for x in g.guard_ms_turns)
        llm_per_turn = g.guard_llm_latency_s.sum() / max(1, n_turns)
        lat.append(f"| {mode} | {med:.3f} | {p95:.3f} | {llm_per_turn:.2f} | {calls} | {g.agent_latency_s.sum() / max(1, calls):.2f} |")
    md.append("\n## Latency\n| mode | guard median ms/turn (rules) | guard p95 ms/turn (rules) | guard LLM classifier s/turn | agent LLM calls | agent mean s/call |\n|---|---|---|---|---|---|\n" + "\n".join(lat) + "\n")
    (out / "results.md").write_text("".join(md), encoding="utf-8")
    print((out / "results.md").read_text(encoding="utf-8"))
    print("LLM stats:", llm.STATS)


if __name__ == "__main__":
    main()
