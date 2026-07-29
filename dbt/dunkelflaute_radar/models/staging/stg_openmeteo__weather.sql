/* get raw response */
select
    zone,
    valid_time,
    ingest_ts,
    ingest_date,
    lat,
    lon,
    wind_mw,
    solar_mw,
    wind_speed_10m,
    wind_speed_80m,
    wind_speed_120m,
    wind_speed_180m,
    shortwave_radiation,
    direct_radiation,
    diffuse_radiation

from {{ source('raw', 'openmeteo_weather') }}