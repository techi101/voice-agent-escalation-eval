"""Load a domain package and give its data/results folders."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ("gp_clinic", "collections")


def load(name: str):
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    return importlib.import_module(f"domains.{name}")


def data_dir(name: str) -> Path:
    return ROOT / "data" / name


def results_dir(name: str, split: str) -> Path:
    return ROOT / "results" / name / split
