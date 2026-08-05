-- Fails if any lead_time is more negative than -24h — Open-Meteo's forecast
-- payload starts at UTC midnight of the ingest day, so a few hours of
-- "already past" data is expected within the first day; anything beyond
-- that signals a real join/data bug.
select *
from {{ ref('int_forecast_vs_actual') }}
where lead_time < interval '-24 hours'