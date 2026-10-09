"""Data loader: generation insights from the dbt warehouse, printed as JSON.

Runs at build time from the repo's uv environment (see `interpreters` in
observablehq.config.js). Averages are in MW. "Fossil" = gas + lignite + hard coal.
"""

import glob
import json
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
# The staging views read parquet via relative paths, so queries must run from the repo root.
os.chdir(ROOT)

con = duckdb.connect(glob.glob("warehouse/*.duckdb")[0], read_only=True)
con.sql("set timezone='UTC'")

# One row per hour: average of the 15-minute readings, by source group.
con.sql("""
    create temp view hourly as
    select
        date_trunc('hour', valid_time) as hour_ts,
        avg(coalesce(wind_onshore_mw, 0) + coalesce(wind_offshore_mw, 0)) as wind,
        avg(solar_mw) as solar,
        avg(coalesce(fossil_gas_mw, 0)) as gas,
        avg(coalesce(fossil_brown_coal_lignite_mw, 0)) as lignite,
        avg(coalesce(fossil_hard_coal_mw, 0)) as hard_coal
    from main.stg_entsoe__generation
    group by 1
""")

# One row per complete day (drops partial days at the edges of the window).
con.sql("""
    create temp view daily as
    select
        date_trunc('day', hour_ts) as day_ts,
        avg(wind) as wind,
        avg(solar) as solar,
        avg(wind + solar) as renewables,
        avg(gas) as gas,
        avg(lignite) as lignite,
        avg(hard_coal) as hard_coal,
        avg(gas + lignite + hard_coal) as fossil
    from hourly
    group by 1
    having count(*) >= 22
""")


def rows(sql: str) -> list[dict]:
    return con.sql(sql).df().round(1).to_dict("records")


out = {
    "summary": rows("""
        select
            strftime(min(day_ts), '%Y-%m-%d') as first_day,
            strftime(max(day_ts), '%Y-%m-%d') as last_day,
            count(*) as n_days,
            avg(wind) as avg_wind, min(wind) as min_wind, max(wind) as max_wind,
            avg(solar) as avg_solar,
            corr(renewables, fossil) as corr_renewables_fossil
        from daily
    """)[0],
    "lowest_day": rows("""
        select strftime(day_ts, '%Y-%m-%d') as day, renewables from daily order by renewables limit 1
    """)[0],
    "by_hour": rows("""
        select hour(hour_ts) as hour_of_day, avg(wind) as wind, avg(solar) as solar,
               avg(gas) as gas, avg(lignite) as lignite, avg(hard_coal) as hard_coal
        from hourly group by 1 order by 1
    """),
    "by_decile": rows("""
        with ranked as (select *, ntile(10) over (order by renewables) as decile from daily)
        select decile, avg(renewables) as renewables, avg(gas) as gas,
               avg(lignite) as lignite, avg(hard_coal) as hard_coal, avg(fossil) as fossil
        from ranked group by decile order by decile
    """),
    "by_month": rows("""
        select strftime(day_ts, '%Y-%m') as month, count(*) as n_days,
               avg(wind) as wind, avg(solar) as solar, avg(fossil) as fossil
        from daily group by 1 order by 1
    """),
}

json.dump(out, sys.stdout, default=str)
