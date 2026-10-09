"""Backfill ENTSO-E actual generation for a range of past days.

Usage:
    uv run python -m ingestion.backfill_entsoe 2026-07-01 2026-10-07

Each day is written with ingest_ts set to the end of that day (UTC), which is
roughly when the daily DAG would have pulled it. This keeps the ingest_date
partitions and the dedup-by-latest-ingest_ts logic in dbt consistent with
real runs. Days that already have a partition are skipped, so it is safe to re-run.
"""

import sys
from datetime import datetime, timezone

import pandas as pd

from ingestion.common.config import RAW_DATA_DIR
from ingestion.entsoe_generation import fetch_generation, parse_generation
from ingestion.common.landing import write_partitioned_parquet


def backfill(start: str, end: str, zone: str = "DE") -> None:
    for day in pd.date_range(start, end, freq="D", tz="Europe/Brussels"):
        ingest_ts = datetime.combine(day.date(), datetime.max.time(), tzinfo=timezone.utc).replace(microsecond=0)
        partition = RAW_DATA_DIR / "entsoe" / "generation" / f"zone={zone}" / f"ingest_date={ingest_ts.date()}"
        if partition.exists():
            print(f"{day.date()}: already there, skipping")
            continue

        try:
            df = parse_generation(fetch_generation(zone, day))
            write_partitioned_parquet(df, "entsoe", "generation", zone, ingest_ts=ingest_ts)
            print(f"{day.date()}: {len(df)} rows")
        except Exception as exc:  # keep going; re-run fills the gaps
            print(f"{day.date()}: FAILED ({exc})")


if __name__ == "__main__":
    backfill(sys.argv[1], sys.argv[2])
