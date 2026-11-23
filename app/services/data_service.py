
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def load_alerts() -> list[dict[str, Any]]:
    file_path = DATA_DIR / "alerts.json"

    with file_path.open("r", encoding="utf-8") as file:
        content = json.load(file)

    return content["data"]


def load_performance_stats() -> list[dict[str, Any]]:
    file_path = DATA_DIR / "performance_stats.json"

    with file_path.open("r", encoding="utf-8") as file:
        content = json.load(file)

    return content["data"]["performance_stats_table"]["ip_table_info"]["data"]


def load_performance_metadata() -> dict[str, Any]:
    """Load the overall performance report metadata."""

    file_path = DATA_DIR / "performance_stats.json"

    with file_path.open("r", encoding="utf-8") as file:
        content = json.load(file)

    return {
        "report_id": content.get("id"),
        "report_date": content.get("date"),
    }


def get_available_zones() -> list[str]:
    records = load_performance_stats()

    return sorted({
        record["site_zone"]
        for record in records
        if record.get("site_zone")
    })


def get_performance_by_zone(zone: str) -> list[dict[str, Any]]:
    if not zone or not zone.strip():
        return []

    requested_zone = zone.strip().casefold()
    records = load_performance_stats()

    return [
        record for record in records
        if (record.get("site_zone") or "").strip().casefold() == requested_zone
    ]