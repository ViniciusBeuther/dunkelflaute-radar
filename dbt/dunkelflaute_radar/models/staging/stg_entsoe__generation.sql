select
    zone,
    valid_time,
    ingest_ts,
    ingest_date,

    "Biomass - Actual Aggregated" as biomass_mw,
    "Fossil Brown coal/Lignite - Actual Aggregated" as fossil_brown_coal_lignite_mw,
    "Fossil Coal-derived gas - Actual Aggregated" as fossil_coal_derived_gas_mw,
    "Fossil Gas - Actual Aggregated" as fossil_gas_mw,
    "Fossil Hard coal - Actual Aggregated" as fossil_hard_coal_mw,
    "Fossil Oil - Actual Aggregated" as fossil_oil_mw,
    "Geothermal - Actual Aggregated" as geothermal_mw,
    "Hydro Pumped Storage - Actual Aggregated" as hydro_pumped_storage_mw,
    "Hydro Pumped Storage - Actual Consumption" as hydro_pumped_storage_consumption_mw,
    "Hydro Run-of-river and poundage - Actual Aggregated" as hydro_run_of_river_mw,
    "Hydro Water Reservoir - Actual Aggregated" as hydro_water_reservoir_mw,
    "Other - Actual Aggregated" as other_mw,
    "Other renewable - Actual Aggregated" as other_renewable_mw,
    "Solar - Actual Aggregated" as solar_mw,
    "Waste - Actual Aggregated" as waste_mw,
    "Wind Offshore - Actual Aggregated" as wind_offshore_mw,
    "Wind Onshore - Actual Aggregated" as wind_onshore_mw

from {{ source('raw', 'entsoe_generation') }}
