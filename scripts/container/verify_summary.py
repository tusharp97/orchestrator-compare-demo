#!/usr/bin/env python3
"""Confirm one or more orchestrator summary files total 612.00."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_TOTAL = 612.00
DATA_DIR = Path("/opt/demo/data")


def main() -> None:
    names = sys.argv[1:]
    if not names:
        raise SystemExit("Usage: verify_summary.py <orchestrator> [orchestrator...]")

    for name in names:
        path = DATA_DIR / f"{name}-summary.json"
        if not path.exists():
            raise SystemExit(f"Missing {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        total = round(sum(row["gross_revenue"] for row in payload["daily_revenue"]), 2)
        print(f"{path.name}: total={total}")
        if total != EXPECTED_TOTAL:
            raise SystemExit(f"Unexpected total in {path.name}: {total}")


if __name__ == "__main__":
    main()
