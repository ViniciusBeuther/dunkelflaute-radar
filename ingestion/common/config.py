"""Shared configuration for ingestion scripts: paths and environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

ENTSOE_API_TOKEN = os.environ.get("ENTSOE_API_TOKEN", "")
ZONES = [zone.strip() for zone in os.environ.get("ZONES", "DE").split(",") if zone.strip()]
