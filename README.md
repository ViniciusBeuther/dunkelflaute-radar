# Dunkelflaute Radar

Daily ELT pipeline for European weather, energy, and air quality data,
forecasting low wind/solar generation windows ("Dunkelflaute") and
quantifying their impact on price, carbon, and air quality. See
[DESCRIPTION.md](DESCRIPTION.md) for the full problem context and target
architecture.

Learning project: built incrementally while learning dbt, Airflow, and
modern data engineering. Current state: **Phase 1 — Solid plumbing**
(ingestion + landing zone + dbt staging, no orchestrator yet).

## Setup

Prerequisite: [uv](https://docs.astral.sh/uv/) installed.

```bash
uv sync                    # creates .venv and installs dependencies, using Python 3.11 (pinned in .python-version)
cp .env.example .env       # fill in ENTSOE_API_TOKEN (see instructions in the file)
```

## Structure

- `ingestion/` — per-source Python ingestion scripts (Open-Meteo, ENTSO-E)
- `data/raw/` — local Parquet landing zone, partitioned by zone/date,
  standing in for an S3 data lake (migration to real S3/MinIO comes later)
- `dbt/dunkelflaute_radar/` — dbt project (staging → intermediate → marts)
- `warehouse/` — local DuckDB file (generated, not versioned)
- `tests/` — unit tests for the ingestion scripts

## Running ingestion (manual, no orchestrator yet)

_To be filled in as milestones M3–M5 of the plan are implemented._
