"""Ingest actual data from ENTSO-E plataform for a bidding zone (GErmany) and load into a raw landing"""

import pandas as pd
from entsoe import EntsoePandasClient

from ingestion.common.config import ENTSOE_API_TOKEN
from ingestion.common.landing import write_partitioned_parquet

ENTSOE_ZONE_CODES = {
    "DE": "DE_LU",
}


def fetch_generation(zone:str, day: pd.Timestamp) -> pd.DataFrame:
    client = EntsoePandasClient(api_key=ENTSOE_API_TOKEN)
    country_code = ENTSOE_ZONE_CODES[zone] # get DE zone based on param
    start = day
    end = day + pd.Timedelta(days=1)

    return client.query_generation(country_code, start=start, end=end)


def parse_generation(raw:pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    # convert tuples to single column
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" - ".join(str(level) for level in col if level) for col in df.columns]
    
    df.index = df.index.tz_convert("UTC")
    df = df.reset_index()
    df = df.rename(columns={df.columns[0]: "valid_time"})

    return df


def ingest(zone:str = "DE") -> None:
    yesterday = pd.Timestamp.now(tz="Europe/Brussels").normalize() - pd.Timedelta(days=1)
    raw = fetch_generation(zone, yesterday)
    df = parse_generation(raw)
    out_path = write_partitioned_parquet(df, source="entsoe", dataset="generation", zone=zone)
    print(f"Wrote {len(df)} rows to {out_path}")

if __name__ == "__main__":
    ingest()