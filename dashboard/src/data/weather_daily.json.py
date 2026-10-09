"""Data loader: daily average weather at each of the 293 capacity-grid points, as JSON.

Shape: {"days": [...], "points": [{"lat", "lon", "wind": [...], "solar": [...]}]}
where wind is the 80 m wind speed (km/h) and solar is shortwave radiation (W/m²),
one value per day in `days`. Only days that also have generation data are kept.

Several forecast runs can cover the same hour (backfill + live runs), so for each
point and hour we keep the run closest to the hour it describes (shortest lead time).
"""

import glob
import json
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)

con = duckdb.connect(glob.glob("warehouse/*.duckdb")[0], read_only=True)
con.sql("set timezone='UTC'")

days = [
    r[0]
    for r in con.sql("""
        select strftime(date_trunc('day', valid_time), '%Y-%m-%d')
        from main.stg_entsoe__generation
        group by 1
        having count(distinct date_trunc('hour', valid_time)) >= 22
        order by 1
    """).fetchall()
]

df = con.sql("""
    with best as (
        select lat, lon, valid_time, wind_speed_80m, shortwave_radiation
        from main.stg_openmeteo__weather
        qualify row_number() over (
            partition by lat, lon, valid_time
            order by abs(epoch(valid_time) - epoch(ingest_ts))
        ) = 1
    )
    select lat, lon,
           strftime(date_trunc('day', valid_time), '%Y-%m-%d') as day,
           avg(wind_speed_80m) as wind, avg(shortwave_radiation) as solar
    from best
    group by 1, 2, 3
""").df()

df = df[df["day"].isin(days)]
index = {d: i for i, d in enumerate(days)}
points: dict[tuple, dict] = {}
for r in df.itertuples(index=False):
    p = points.setdefault(
        (r.lat, r.lon),
        {"lat": r.lat, "lon": r.lon, "wind": [None] * len(days), "solar": [None] * len(days)},
    )
    p["wind"][index[r.day]] = round(r.wind, 1)
    p["solar"][index[r.day]] = round(r.solar, 1)

json.dump({"days": days, "points": list(points.values())}, sys.stdout)
