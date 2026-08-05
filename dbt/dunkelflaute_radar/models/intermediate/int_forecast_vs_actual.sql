with weather as (
    select * from {{ ref('int_weather_national') }}
),

actuals_ranked as (
    select
        zone,
        valid_time,
        wind_onshore_mw + coalesce(wind_offshore_mw, 0) as actual_wind_mw,
        solar_mw as actual_solar_mw,
        row_number() over (partition by zone, valid_time order by ingest_ts desc) as rn
        from {{ ref('stg_entsoe__generation') }}
),

actuals as (
    select zone, valid_time, actual_wind_mw, actual_solar_mw
    from actuals_ranked
    where rn = 1
)

select
    weather.zone,
    weather.valid_time,
    weather.ingest_ts,
    weather.valid_time - weather.ingest_ts as lead_time,

    weather.wind_speed_10m_weighted,
    weather.wind_speed_80m_weighted,
    weather.wind_speed_120m_weighted,
    weather.wind_speed_180m_weighted,
    weather.shortwave_radiation_weighted,
    weather.direct_radiation_weighted,
    weather.diffuse_radiation_weighted,
    weather.total_wind_mw,
    weather.total_solar_mw,

    actuals.actual_wind_mw,
    actuals.actual_solar_mw

from weather
inner join actuals
    on weather.zone = actuals.zone
    and weather.valid_time = actuals.valid_time