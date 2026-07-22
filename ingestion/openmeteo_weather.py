"""Ingest Open-Meteo wind/irradiance forecasts for a bidding zone into the raw landing zone.

Phase 1 simplification: each zone is represented by a single representative
lat/lon point rather than a capacity-weighted grid. Real installed wind/solar
capacity is unevenly distributed within a zone (e.g. Germany's wind capacity
is concentrated in the north), so this is a known source of error to revisit
in Phase 2.
"""

import pandas as pd
import requests

from ingestion.common.landing import write_partitioned_parquet

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Single representative point per zone (see module docstring for the caveat).
ZONE_COORDINATES = {
    "DE": {"latitude": 51.1657, "longitude": 10.4515},  # geographic center of Germany
}

HOURLY_VARIABLES = [
    "wind_speed_10m",
    "wind_speed_80m",
    "wind_speed_120m",
    "wind_speed_180m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
]


def fetch_forecast(zone: str, forecast_days: int = 16) -> dict:
    coordinates = ZONE_COORDINATES[zone]
    response = requests.get(
        OPEN_METEO_URL,
        params={
            **coordinates,
            "hourly": ",".join(HOURLY_VARIABLES),
            "forecast_days": forecast_days,
            "timezone": "GMT",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def parse_forecast(payload: dict) -> pd.DataFrame:
    hourly = pd.DataFrame(payload["hourly"])
    hourly = hourly.rename(columns={"time": "valid_time"})
    hourly["valid_time"] = pd.to_datetime(hourly["valid_time"], utc=True)
    return hourly


def ingest(zone: str = "DE") -> None:
    payload = fetch_forecast(zone)
    df = parse_forecast(payload)
    out_path = write_partitioned_parquet(df, source="openmeteo", dataset="weather_forecast", zone=zone)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    ingest()
