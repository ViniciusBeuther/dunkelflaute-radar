# Dunkelflaute Radar

Daily ELT pipeline for European weather and energy data, forecasting low
wind/solar generation windows ("Dunkelflaute") and quantifying forecast
accuracy against real generation outcomes.

Learning project: built incrementally while learning dbt, Airflow, and
modern data engineering. **Phase 1 — solid plumbing — is complete**:
ingestion, partitioned Parquet landing zone, dbt staging models with tests
and source freshness, and orchestration via Airflow (Docker), including
`dbt run`/`dbt test` as scheduled tasks. **Phase 2 is underway**: weather is
now sampled across a capacity-weighted 0.5°×0.5° grid (293 points across
Germany, weighted by real installed wind/solar capacity from the German
Marktstammdatenregister) instead of a single representative point.
Forecast-skill scoring, a rigorous Dunkelflaute event definition, cross-zone
interconnection with France, and AWS/Terraform migration are still planned.

## Setup

Prerequisites: [uv](https://docs.astral.sh/uv/), Docker Desktop (only needed
to run the Airflow stack).

```bash
uv sync                    # creates .venv and installs dependencies, using Python 3.11 (pinned in .python-version)
cp .env.example .env       # fill in ENTSOE_API_TOKEN (see instructions in the file)
```

## Structure

- `ingestion/` — per-source Python ingestion scripts (Open-Meteo, ENTSO-E)
- `data/raw/` — local Parquet landing zone, partitioned by `zone`/`ingest_date`,
  standing in for an S3 data lake (migration to real S3 is a Phase 2 item)
- `dbt/dunkelflaute_radar/` — dbt project (staging models + tests today;
  intermediate/marts come in Phase 2)
- `airflow/` — Docker Compose Airflow stack; DAG at
  `airflow/dags/dunkelflaute_ingestion.py`
- `warehouse/` — local DuckDB file (generated, not versioned)
- `tests/` — unit tests for the ingestion scripts

## Running ingestion

**Standalone**, no orchestrator:

```bash
uv run python -m ingestion.openmeteo_weather
uv run python -m ingestion.entsoe_generation
```

**Via Airflow** (schedules both daily and runs them for you):

```bash
cd airflow
docker compose up -d
```

Then open `http://localhost:8080` (login `airflow`/`airflow`), unpause
`dunkelflaute_ingestion`, and trigger it — or just let it run on its own
`@daily` schedule.

## Running dbt

Every `dbt` command must be run **from the repo root**, with both flags
below (relative paths in `profiles.yml`/`_sources.yml` resolve against the
current working directory, not the file's location):

```bash
uv run dbt run  --project-dir dbt/dunkelflaute_radar --profiles-dir dbt/dunkelflaute_radar
uv run dbt test --project-dir dbt/dunkelflaute_radar --profiles-dir dbt/dunkelflaute_radar
```

`dbt docs serve` also needs an explicit `--port` (its default, 8080, collides
with the Airflow webserver):

```bash
uv run dbt docs generate --project-dir dbt/dunkelflaute_radar --profiles-dir dbt/dunkelflaute_radar
uv run dbt docs serve --port 8081 --project-dir dbt/dunkelflaute_radar --profiles-dir dbt/dunkelflaute_radar
```
