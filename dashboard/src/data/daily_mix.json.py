"""Data loader: German generation mix per complete day, in average MW, as JSON.

Groups: wind, solar, gas, lignite (brown coal), hard_coal, other
(biomass, hydro, geothermal, other renewables, pumped-storage output, oil, waste, rest).
Days with fewer than 22 hourly readings (edges of the window) are dropped.
"""

import glob
import json
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)  # the staging views read parquet through relative paths

con = duckdb.connect(glob.glob("warehouse/*.duckdb")[0], read_only=True)
con.sql("set timezone='UTC'")

df = con.sql("""
    with hourly as (
        select
            date_trunc('hour', valid_time) as hour_ts,
            avg(coalesce(wind_onshore_mw, 0) + coalesce(wind_offshore_mw, 0)) as wind,
            avg(solar_mw) as solar,
            avg(coalesce(fossil_gas_mw, 0)) as gas,
            avg(coalesce(fossil_brown_coal_lignite_mw, 0)) as lignite,
            avg(coalesce(fossil_hard_coal_mw, 0)) as hard_coal,
            avg(
                coalesce(biomass_mw, 0) + coalesce(hydro_run_of_river_mw, 0)
                + coalesce(hydro_water_reservoir_mw, 0) + coalesce(hydro_pumped_storage_mw, 0)
                + coalesce(geothermal_mw, 0) + coalesce(other_renewable_mw, 0)
                + coalesce(fossil_oil_mw, 0) + coalesce(fossil_coal_derived_gas_mw, 0)
                + coalesce(waste_mw, 0) + coalesce(other_mw, 0)
            ) as other
        from main.stg_entsoe__generation
        group by 1
    )
    select
        strftime(date_trunc('day', hour_ts), '%Y-%m-%d') as day,
        round(avg(wind)) as wind, round(avg(solar)) as solar, round(avg(gas)) as gas,
        round(avg(lignite)) as lignite, round(avg(hard_coal)) as hard_coal, round(avg(other)) as other
    from hourly
    group by 1
    having count(*) >= 22
    order by 1
""").df()

json.dump(df.to_dict("records"), sys.stdout)
