"""Build the synthetic dataset: specs -> LLM-written caller turns -> checks -> noise.

Usage: python scripts/build_dataset.py [--limit N]
Writes data/scenarios.jsonl (all specs, ground truth) and data/transcripts.jsonl
(accepted transcripts). LLM responses are cached, so a rerun is free.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gpeval import llm  # noqa: E402
from gpeval.generate import build_transcripts  # noqa: E402
from gpeval.scenarios import build_scenarios  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    scen = build_scenarios()
    if args.limit:
        scen = scen[: args.limit]
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    with (data / "scenarios.jsonl").open("w", encoding="utf-8") as f:
        for s in scen:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
    rows = build_transcripts(scen)
    with (data / "transcripts.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"specs={len(scen)} accepted={len(rows)} dropped={len(scen) - len(rows)}")
    print("by split:", Counter(r["split"] for r in rows))
    print("LLM stats:", llm.STATS)


if __name__ == "__main__":
    main()
