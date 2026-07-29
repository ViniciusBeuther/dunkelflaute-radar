"""Ingest Open-Meteo wind/irradiance forecasts for a bidding zone into the raw landing zone.

Phase 1 simplification: each zone is represented by a single representative
lat/lon point rather than a capacity-weighted grid. Real installed wind/solar
capacity is unevenly distributed within a zone (e.g. Germany's wind capacity
is concentrated in the north), so this is a known source of error to revisit
in Phase 2.
"""

import pandas as pd
import requests
from pathlib import Path
from ingestion.common.landing import write_partitioned_parquet

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

CAPACITY_GRID_PATH = Path("dbt/dunkelflaute_radar/seeds/capacity_grid.csv")

HOURLY_VARIABLES = [
    "wind_speed_10m",
    "wind_speed_80m",
    "wind_speed_120m",
    "wind_speed_180m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
]

def load_capacity_grid(path: Path = CAPACITY_GRID_PATH) -> pd.DataFrame:
    return pd.read_csv(path)

def fetch_forecast(grid: pd.DataFrame, forecast_days: int = 16) -> dict:
    response = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": ",".join(grid["lat"].astype(str)),
            "longitude": ",".join(grid["lon"].astype(str)),
            "hourly": ",".join(HOURLY_VARIABLES),
            "forecast_days": forecast_days,
            "timezone": "GMT",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def parse_forecast(payload: list[dict], grid: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for row, location_payload in zip(grid.itertuples(index=False), payload):
        hourly = pd.DataFrame(location_payload["hourly"])
        hourly = hourly.rename(columns={"time": "valid_time"})
        hourly["valid_time"] = pd.to_datetime(hourly["valid_time"], utc=True)
        hourly["lat"] = row.lat
        hourly["lon"] = row.lon
        hourly["wind_mw"] = row.wind_mw
        hourly["solar_mw"] = row.solar_mw
        frames.append(hourly)
    
    return pd.concat(frames, ignore_index=True)


def ingest(zone: str = "DE") -> None:
    grid = load_capacity_grid()
    payload = fetch_forecast(grid)
    df = parse_forecast(payload, grid)
    out_path = write_partitioned_parquet(df, source="openmeteo", dataset="weather_forecast", zone=zone)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    ingest()
