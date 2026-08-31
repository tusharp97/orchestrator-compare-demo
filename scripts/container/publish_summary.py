#!/usr/bin/env python3
"""Write the shared shop-revenue JSON artifact for one orchestrator."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb

EXPECTED_TOTAL = 612.00


def main() -> None:
    orchestrator = os.environ["ORCHESTRATOR"]
    data_dir = Path(os.environ.get("DEMO_DATA_DIR", "/opt/demo/data"))
    database = os.environ["DUCKDB_PATH"]
    data_dir.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(database, read_only=True) as connection:
        rows = connection.execute(
            """
            select order_date, order_count, customer_count, gross_revenue
            from fct_daily_revenue
            order by order_date
            """
        ).fetchall()

    summary = {
        "orchestrator": orchestrator,
        "database": database,
        "daily_revenue": [
            {
                "order_date": str(row[0]),
                "order_count": row[1],
                "customer_count": row[2],
                "gross_revenue": float(row[3]),
            }
            for row in rows
        ],
    }
    report_path = data_dir / f"{orchestrator}-summary.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    total = round(sum(item["gross_revenue"] for item in summary["daily_revenue"]), 2)
    print(f"{report_path.name}: total={total}")
    if total != EXPECTED_TOTAL:
        raise SystemExit(f"Unexpected total in {report_path.name}: {total}")


if __name__ == "__main__":
    main()
