from datetime import datetime
import subprocess
from airflow.sdk import dag, task

from ingestion.entsoe_generation import ingest as ingest_entsoe_data
from ingestion.openmeteo_weather import ingest as ingest_weather_data

DBT_FLAGS = [
    "--project-dir", "/opt/airflow/dbt/dunkelflaute_radar",
    "--profiles-dir", "/opt/airflow/dbt/dunkelflaute_radar",    
]

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

    @task
    def dbt_run():
        subprocess.run(["dbt", "run", *DBT_FLAGS], check=True)

    @task
    def dbt_test():
        subprocess.run(["dbt", "test", *DBT_FLAGS], check=True)

    ingest_weather() >> ingest_entsoe() >> dbt_run() >> dbt_test()
dunkelflaute_ingestion()