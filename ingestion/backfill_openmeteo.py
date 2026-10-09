"""Backfill Open-Meteo weather for past days using the Historical Forecast API.

Usage:
    uv run python -m ingestion.backfill_openmeteo 2026-07-01 2026-10-07

Limitation: the Historical Forecast API returns one stitched forecast per
valid_time (the model's early-hours output), not every forecast run we would
have pulled live. So each backfilled day gets ingest_ts = 00:00 UTC of that
day and lead times of 0-23h. Longer lead times only accumulate from live runs.
Days that already have a partition are skipped, so it is safe to re-run.
"""

import sys
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from ingestion.common.config import RAW_DATA_DIR
from ingestion.common.landing import write_partitioned_parquet
from ingestion.openmeteo_weather import HOURLY_VARIABLES, load_capacity_grid, parse_forecast

HISTORICAL_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
CHUNK_DAYS = 7  # keeps each request (293 points x days) small enough to avoid rate limits


def fetch_historical(grid: pd.DataFrame, start: str, end: str) -> list[dict]:
    for attempt in range(5):
        response = requests.get(
            HISTORICAL_URL,
            params={
                "latitude": ",".join(grid["lat"].astype(str)),
                "longitude": ",".join(grid["lon"].astype(str)),
                "hourly": ",".join(HOURLY_VARIABLES),
                "start_date": start,
                "end_date": end,
                "timezone": "GMT",
            },
            timeout=120,
        )
        if response.status_code == 429:  # rate limited: wait and retry
            time.sleep(60 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Still rate limited after retries for {start} to {end}")


def backfill(start: str, end: str, zone: str = "DE") -> None:
    grid = load_capacity_grid()
    days = pd.date_range(start, end, freq="D")

    for i in range(0, len(days), CHUNK_DAYS):
        chunk = days[i : i + CHUNK_DAYS]
        pending = [
            d for d in chunk
            if not (RAW_DATA_DIR / "openmeteo" / "weather_forecast" / f"zone={zone}" / f"ingest_date={d.date()}").exists()
        ]
        if not pending:
            print(f"{chunk[0].date()} to {chunk[-1].date()}: already there, skipping")
            continue

        try:
            payload = fetch_historical(grid, str(pending[0].date()), str(pending[-1].date()))
            df = parse_forecast(payload, grid)
        except Exception as exc:  # keep going; re-run fills the gaps
            print(f"{pending[0].date()} to {pending[-1].date()}: FAILED ({exc})")
            continue

        for day in pending:
            day_df = df[df["valid_time"].dt.date == day.date()]
            if day_df.empty:
                continue
            ingest_ts = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            write_partitioned_parquet(day_df, "openmeteo", "weather_forecast", zone, ingest_ts=ingest_ts)
            print(f"{day.date()}: {len(day_df)} rows")
        time.sleep(5)


if __name__ == "__main__":
    backfill(sys.argv[1], sys.argv[2])
