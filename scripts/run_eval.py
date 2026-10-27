"""Run the evaluation for one domain and write results.

Usage:
  python scripts/run_eval.py --domain gp_clinic --split dev     # for tuning the guard
  python scripts/run_eval.py --domain gp_clinic --split test    # headline numbers
  python scripts/run_eval.py --domain gp_clinic --split test --modes baseline guard guard_llm
Outputs go to results/<domain>/<split>/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaeval import domain, llm  # noqa: E402
from vaeval.metrics import guard_latency, summary_table  # noqa: E402
from vaeval.runner import run_all  # noqa: E402


def to_markdown(df: pd.DataFrame, cols) -> str:
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n" for _, r in df.iterrows())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=domain.DOMAINS)
    ap.add_argument("--split", default="test", choices=["dev", "test", "all"])
    ap.add_argument("--modes", nargs="+", default=["baseline", "guard"])
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    dom = domain.load(args.domain)
    COLS = [m[0] for m in dom.METRICS] + ["turns_to_handoff_mean"]
    NAMES = {m[0]: m[1] for m in dom.METRICS}
    NAMES["turns_to_handoff_mean"] = "Mean caller turns until handoff"

    rows = [json.loads(line) for line in (domain.data_dir(args.domain) / "transcripts.jsonl").open(encoding="utf-8")]
    if args.split != "all":
        rows = [r for r in rows if r["split"] == args.split]
    out = domain.results_dir(args.domain, args.split)
    out.mkdir(parents=True, exist_ok=True)

    frames = []
    for mode in args.modes:
        t0 = time.time()
        res = run_all(rows, mode, dom, workers=args.workers)
        df = pd.DataFrame(res)
        df.to_csv(out / f"calls_{mode}.csv", index=False, encoding="utf-8")
        frames.append(df)
        print(f"{mode}: {len(df)} calls in {time.time() - t0:.0f}s; LLM {llm.STATS}", flush=True)
    df = pd.concat(frames)

    overall = summary_table(df, dom)
    by_slice = summary_table(df, dom, by="slice")
    overall.to_csv(out / "summary_overall.csv", index=False)
    by_slice.to_csv(out / "summary_by_slice.csv", index=False)

    md = [f"# Results: {dom.TITLE}, {args.split} split ({len(rows)} scenarios)\n",
          f"Agent model: {dom.AGENT_MODEL}. Cells: k/n = rate [Wilson 95% interval]. "
          "Higher is better except false escalation, unneeded transfer and turns.\n",
          "## Overall\n"]
    t = overall.copy()
    md.append(to_markdown(t.rename(columns=NAMES), ["mode"] + [NAMES[c] for c in COLS]))
    for metric in COLS[:-1]:
        md.append(f"\n## {NAMES[metric]} by slice\n")
        piv = by_slice.pivot(index="group", columns="mode", values=metric).reset_index()
        md.append(to_markdown(piv, list(piv.columns)))
    # paired turns-to-handoff: only calls handed off in BOTH baseline and the other mode
    if "baseline" in args.modes:
        b = df[df["mode"] == "baseline"].set_index("id")
        md.append("\n## Turns to handoff, paired (calls handed off in both modes)\n| mode | n pairs | baseline mean turns | mode mean turns |\n|---|---|---|---|\n")
        for mode in [m for m in args.modes if m != "baseline"]:
            g = df[df["mode"] == mode].set_index("id")
            ids = [i for i in g.index if g.loc[i, "group"] in ("human", "capture")
                   and g.loc[i, "final_action"] == "transfer_to_human" and b.loc[i, "final_action"] == "transfer_to_human"]
            if ids:
                md.append(f"| {mode} | {len(ids)} | {b.loc[ids, 'turns_heard'].mean():.2f} | {g.loc[ids, 'turns_heard'].mean():.2f} |\n")
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
