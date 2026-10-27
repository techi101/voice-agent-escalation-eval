"""Build a domain's synthetic dataset: specs -> LLM-written caller turns -> checks -> noise.

Usage: python scripts/build_dataset.py --domain gp_clinic [--limit N]
Writes data/<domain>/scenarios.jsonl (all specs, ground truth) and
data/<domain>/transcripts.jsonl (accepted transcripts). LLM responses are
cached, so a rerun is free.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaeval import domain, llm  # noqa: E402
from vaeval.generate import build_transcripts  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=domain.DOMAINS)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-attempts", type=int, default=3, help="write/check rounds; failed specs are dropped after the last")
    args = ap.parse_args()
    dom = domain.load(args.domain)
    scen = dom.build_scenarios()
    if args.limit:
        scen = scen[: args.limit]
    data = domain.data_dir(args.domain)
    data.mkdir(parents=True, exist_ok=True)
    with (data / "scenarios.jsonl").open("w", encoding="utf-8") as f:
        for s in scen:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
    rows = build_transcripts(dom, scen, data, max_attempts=args.max_attempts)
    with (data / "transcripts.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"specs={len(scen)} accepted={len(rows)} dropped={len(scen) - len(rows)}")
    print("by split:", Counter(r["split"] for r in rows))
    print("LLM stats:", llm.STATS)


if __name__ == "__main__":
    main()
