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


def current_utc_hour() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d-%H")


def current_hour_bucket() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")


def previous_hour_bucket() -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d-%H")


async def wait_if_paused():
    pause_path = Path(PAUSE_FILE)

    while pause_path.exists():
        logger.warning(f"Paused because {PAUSE_FILE} exists")
        await asyncio.sleep(30)


async def main():
    logger.info("Starting Wynn analytics scraper")

    api = WynnAPI()
    sqlite_store = SQLiteStore()
    bq = BigQueryClient()

    last_raid_scan_hour = None

    try:
        async with await api.create_session() as session:
            while True:
                await wait_if_paused()

                logger.info("Starting online player poll")

                await collect_online_players_once(
                    api=api,
                    session=session,
                    sqlite_store=sqlite_store,
                    bq=bq,
                    hour_bucket=current_hour_bucket(),
                )

                current_hour = current_utc_hour()

                if current_hour != last_raid_scan_hour:
                    logger.info(f"Starting hourly raid scan for hour={current_hour}")

                    scan_hour = previous_hour_bucket()

                    await collect_raid_deltas_once(
                        api=api,
                        session=session,
                        sqlite_store=sqlite_store,
                        bq=bq,
                        hour_bucket=scan_hour,
                    )

                    last_raid_scan_hour = current_hour

                logger.info(f"Sleeping for {ONLINE_POLL_SECONDS} seconds")
                await asyncio.sleep(ONLINE_POLL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down")

    except Exception:
        logger.exception("Fatal error in main loop")

    finally:
        sqlite_store.close()
        logger.info("Scraper stopped")


if __name__ == "__main__":
    asyncio.run(main())