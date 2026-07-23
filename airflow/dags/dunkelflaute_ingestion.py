from datetime import datetime

from airflow.sdk import dag, task

from ingestion.entsoe_generation import ingest as ingest_entsoe_data
from ingestion.openmeteo_weather import ingest as ingest_weather_data

@dag(
    dag_id="dunkelflaute_ingestion",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["dunkelflaute-radar"],
)
def dunkelflaute_ingestion():
    @task
    def ingest_weather():
        ingest_weather_data()

    @task
    def ingest_entsoe():
        ingest_entsoe_data()

    ingest_weather() >> ingest_entsoe()

dunkelflaute_ingestion()