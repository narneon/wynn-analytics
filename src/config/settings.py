from pathlib import Path
from dotenv import load_dotenv
import os


# Assumes you run commands from project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


def _get_list_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


# Paths
LOCAL_DB_PATH = Path(os.getenv("LOCAL_DB_PATH", "data/players.db"))
LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs/scraper.log"))
PAUSE_FILE = Path(os.getenv("PAUSE_FILE", "data/PAUSE"))

# Google / BigQuery
GCP_PROJECT_ID = _get_required_env("GCP_PROJECT_ID")
BQ_DATASET = _get_required_env("BQ_DATASET")
BQ_RAID_TABLE = os.getenv("BQ_RAID_TABLE", "hourly_raid_data")
BQ_ONLINE_TABLE = os.getenv("BQ_ONLINE_TABLE", "online_player_count")
BQ_DAILY_TABLE = os.getenv("BQ_DAILY_TABLE", "daily_raid_data")

# Wynn API
WYNN_API_KEYS = _get_list_env("WYNN_API_KEYS")

# Runtime tuning
ONLINE_POLL_SECONDS = _get_int_env("ONLINE_POLL_SECONDS", 300)
GLOBAL_CONCURRENCY = _get_int_env("GLOBAL_CONCURRENCY", 40)
REQUEST_TIMEOUT_SECONDS = _get_int_env("REQUEST_TIMEOUT_SECONDS", 30)

# Logging
LOG_MAX_BYTES = _get_int_env("LOG_MAX_BYTES", 5_000_000)
LOG_BACKUP_COUNT = _get_int_env("LOG_BACKUP_COUNT", 5)

# Dry Run
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# Discord / reporting
DISCORD_WEBHOOK_URL = _get_required_env("DISCORD_WEBHOOK_URL")

DAILY_DIGEST_HOUR_UTC = _get_int_env("DAILY_DIGEST_HOUR_UTC", 17)
DAILY_DIGEST_MINUTE_UTC = _get_int_env("DAILY_DIGEST_MINUTE_UTC", 30)

# Weekday on which the weekly digest fires (0=Mon … 6=Sun, default 4=Fri)
WEEKLY_DIGEST_WEEKDAY = _get_int_env("WEEKLY_DIGEST_WEEKDAY", 4)

REPORT_OUTPUT_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", "data/reports"))