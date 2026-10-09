"""Data loader: installed wind/solar capacity per grid point, printed as JSON.

Observable runs this at build time and serves its output as /data/capacity.json.
Source: the dbt seed that Open-Meteo ingestion also uses, so map and pipeline agree.
"""

import csv
import json
import sys
from pathlib import Path

SEED = Path(__file__).resolve().parents[3] / "dbt/dunkelflaute_radar/seeds/capacity_grid.csv"

with open(SEED, newline="") as f:
    points = [
        {
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "wind_mw": float(row["wind_mw"]),
            "solar_mw": float(row["solar_mw"]),
        }
        for row in csv.DictReader(f)
    ]

json.dump(points, sys.stdout)
