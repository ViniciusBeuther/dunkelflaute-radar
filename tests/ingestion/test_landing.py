from datetime import datetime, timezone

import pandas as pd
import pytest

from ingestion.common.landing import write_partitioned_parquet


@pytest.fixture
def fake_df() -> pd.DataFrame:
    return pd.DataFrame({"valid_time": ["2026-07-21T00:00:00Z"], "wind_speed_10m": [5.4]})


def test_writes_to_expected_partition_path(tmp_path, fake_df):
    ingest_ts = datetime(2026, 7, 20, 6, 0, 0, tzinfo=timezone.utc)

    out_path = write_partitioned_parquet(
        fake_df, source="openmeteo", dataset="weather_forecast", zone="DE",
        ingest_ts=ingest_ts, base_dir=tmp_path,
    )

    expected = (
        tmp_path / "openmeteo" / "weather_forecast" / "zone=DE"
        / "ingest_date=2026-07-20" / "ingest_ts=2026-07-20T06-00-00Z.parquet"
    )
    assert out_path == expected
    assert out_path.exists()


def test_stamps_ingest_ts_column(tmp_path, fake_df):
    ingest_ts = datetime(2026, 7, 20, 6, 0, 0, tzinfo=timezone.utc)

    out_path = write_partitioned_parquet(
        fake_df, source="openmeteo", dataset="weather_forecast", zone="DE",
        ingest_ts=ingest_ts, base_dir=tmp_path,
    )

    written = pd.read_parquet(out_path)
    assert (written["ingest_ts"] == ingest_ts).all()
    assert "valid_time" in written.columns


def test_two_runs_same_day_create_two_partitions(tmp_path, fake_df):
    first_ts = datetime(2026, 7, 20, 6, 0, 0, tzinfo=timezone.utc)
    second_ts = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)

    first_path = write_partitioned_parquet(
        fake_df, source="openmeteo", dataset="weather_forecast", zone="DE",
        ingest_ts=first_ts, base_dir=tmp_path,
    )
    second_path = write_partitioned_parquet(
        fake_df, source="openmeteo", dataset="weather_forecast", zone="DE",
        ingest_ts=second_ts, base_dir=tmp_path,
    )

    assert first_path != second_path
    assert first_path.exists() and second_path.exists()


def test_rejects_empty_dataframe(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        write_partitioned_parquet(
            pd.DataFrame(), source="openmeteo", dataset="weather_forecast", zone="DE",
            base_dir=tmp_path,
        )


def test_rejects_naive_ingest_ts(tmp_path, fake_df):
    with pytest.raises(ValueError, match="timezone-aware"):
        write_partitioned_parquet(
            fake_df, source="openmeteo", dataset="weather_forecast", zone="DE",
            ingest_ts=datetime(2026, 7, 20, 6, 0, 0), base_dir=tmp_path,
        )
