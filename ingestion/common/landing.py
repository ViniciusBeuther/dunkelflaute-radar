"""Shared contract for writing raw data into the local landing zone.

Every ingestion script writes through `write_partitioned_parquet` so the raw
zone stays consistent: partitioned by `ingest_date` (the day we pulled the
data, not the date it describes), stamped with `ingest_ts`, and append-only.
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingestion.common.config import RAW_DATA_DIR


def write_partitioned_parquet(
    df: pd.DataFrame,
    source: str,
    dataset: str,
    zone: str,
    ingest_ts: datetime | None = None,
    base_dir: Path = RAW_DATA_DIR,
) -> Path:
    if df.empty:
        raise ValueError("Refusing to write an empty DataFrame to the landing zone")

    ingest_ts = ingest_ts or datetime.now(timezone.utc)
    if ingest_ts.tzinfo is None:
        raise ValueError("ingest_ts must be timezone-aware (UTC)")

    stamped = df.copy()
    stamped["ingest_ts"] = ingest_ts

    ingest_date = ingest_ts.date().isoformat()
    ingest_ts_slug = ingest_ts.strftime("%Y-%m-%dT%H-%M-%SZ")

    partition_dir = base_dir / source / dataset / f"zone={zone}" / f"ingest_date={ingest_date}"
    partition_dir.mkdir(parents=True, exist_ok=True)

    out_path = partition_dir / f"ingest_ts={ingest_ts_slug}.parquet"
    stamped.to_parquet(out_path, engine="pyarrow", index=False)

    return out_path
