select
    zone, 
    valid_time,
    ingest_ts,

    sum(wind_speed_10m * wind_mw) / sum(wind_mw) as wind_speed_10m_weighted,
    sum(wind_speed_80m * wind_mw) / sum(wind_mw) as wind_speed_80m_weighted,
    sum(wind_speed_120m * wind_mw) / sum(wind_mw) as wind_speed_120m_weighted,
    sum(wind_speed_180m * wind_mw) / sum(wind_mw) as wind_speed_180m_weighted,

    sum(shortwave_radiation * solar_mw) / sum(solar_mw) as shortwave_radiation_weighted,
    sum(direct_radiation * solar_mw) / sum(solar_mw) as direct_radiation_weighted,
    sum(diffuse_radiation * solar_mw) / sum(solar_mw) as diffuse_radiation_weighted,

    sum(wind_mw) as total_wind_mw,
    sum(solar_mw) as total_solar_mw

    from {{ ref('stg_openmeteo__weather') }}

    group by zone, valid_time, ingest_ts