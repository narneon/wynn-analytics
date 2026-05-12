import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.api.wynn_api import WynnAPI
from src.collectors.online_players import collect_online_players_once
from src.collectors.raid_tracker import collect_raid_deltas_once
from src.config.settings import ONLINE_POLL_SECONDS, PAUSE_FILE
from src.database.bigquery_client import BigQueryClient
from src.database.sqlite_store import SQLiteStore
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


def utc_now():
    return datetime.now(timezone.utc)


def current_hour_bucket() -> str:
    return utc_now().strftime("%Y-%m-%d-%H")


def previous_hour_bucket() -> str:
    return (utc_now() - timedelta(hours=1)).strftime("%Y-%m-%d-%H")


def seconds_until_next_boundary(interval_seconds: int) -> float:
    now = utc_now()
    seconds_since_hour = (
        now.minute * 60
        + now.second
        + now.microsecond / 1_000_000
    )

    remainder = seconds_since_hour % interval_seconds
    sleep_seconds = interval_seconds - remainder

    if sleep_seconds <= 0:
        return interval_seconds

    return sleep_seconds


def seconds_until_next_hour() -> float:
    now = utc_now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return (next_hour - now).total_seconds()


async def wait_if_paused():
    pause_path = Path(PAUSE_FILE)

    while pause_path.exists():
        logger.warning(f"Paused because {PAUSE_FILE} exists")
        await asyncio.sleep(30)


async def online_poll_loop(api, session, sqlite_store, bq):
    while True:
        await wait_if_paused()

        hour_bucket = current_hour_bucket()

        logger.info(f"Starting online player poll for hour_bucket={hour_bucket}")

        await collect_online_players_once(
            api=api,
            session=session,
            sqlite_store=sqlite_store,
            bq=bq,
            hour_bucket=hour_bucket,
        )

        sleep_seconds = seconds_until_next_boundary(ONLINE_POLL_SECONDS)

        logger.info(f"Sleeping {sleep_seconds:.1f}s until next online poll boundary")
        await asyncio.sleep(sleep_seconds)


async def raid_scan_loop(api, session, sqlite_store, bq):
    # Do not scan immediately on startup.
    # Wait until the next real hour boundary.
    sleep_seconds = seconds_until_next_hour()
    logger.info(f"First raid scan scheduled in {sleep_seconds:.1f}s")
    await asyncio.sleep(sleep_seconds)

    while True:
        await wait_if_paused()

        scan_bucket = previous_hour_bucket()

        logger.info(f"Starting hourly raid scan for previous hour_bucket={scan_bucket}")

        await collect_raid_deltas_once(
            api=api,
            session=session,
            sqlite_store=sqlite_store,
            bq=bq,
            hour_bucket=scan_bucket,
        )

        sleep_seconds = seconds_until_next_hour()

        logger.info(f"Sleeping {sleep_seconds:.1f}s until next raid scan boundary")
        await asyncio.sleep(sleep_seconds)


async def main():
    logger.info("Starting Wynn analytics scraper")

    api = WynnAPI()
    sqlite_store = SQLiteStore()
    bq = BigQueryClient()

    try:
        async with await api.create_session() as session:
            await asyncio.gather(
                online_poll_loop(api, session, sqlite_store, bq),
                raid_scan_loop(api, session, sqlite_store, bq),
            )

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down")

    except Exception:
        logger.exception("Fatal error in main loop")

    finally:
        sqlite_store.close()
        logger.info("Scraper stopped")


if __name__ == "__main__":
    asyncio.run(main())