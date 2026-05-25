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

from src.reports.daily_digest import DailyDigestService
from src.reports.chart_images import generate_raid_digest_images
from src.reports.discord_client import send_discord_files
from src.reports.ultimate_usage import compute_ultimate_usage_counts
from src.config.settings import DAILY_DIGEST_HOUR_UTC, DAILY_DIGEST_MINUTE_UTC

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


def seconds_until_next_daily_digest() -> float:
    now = utc_now()

    next_digest = now.replace(
        hour=DAILY_DIGEST_HOUR_UTC,
        minute=DAILY_DIGEST_MINUTE_UTC,
        second=0,
        microsecond=0,
    )

    if now >= next_digest:
        next_digest += timedelta(days=1)

    return (next_digest - now).total_seconds()


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


async def daily_digest_loop(api, session):
    digest_service = DailyDigestService()

    while True:
        sleep_seconds = seconds_until_next_daily_digest()
        logger.info(f"Daily digest scheduled in {sleep_seconds:.1f}s")
        await asyncio.sleep(sleep_seconds)

        await wait_if_paused()

        try:
            logger.info("Starting daily Discord digest")

            digest_rows = digest_service.fetch_daily_digest_rows()
            raider_rows = digest_service.fetch_daily_raider_rows()

            ult_counts = await compute_ultimate_usage_counts(
                api=api,
                session=session,
                raider_rows=raider_rows,
            )

            for row in digest_rows:
                key = (row["raid"], row["archetype"])
                row["ult_uses"] = ult_counts.get(key, 0)

            digest_service.insert_daily_digest_rows(digest_rows)

            image_paths = generate_raid_digest_images(digest_rows)

            current_date = datetime.now(timezone.utc).strftime("%m/%d/%Y")

            message = (
                "Daily Wynncraft Raid Report\n"
                f"Date: {current_date}\n"
                "Made by: Wynn Analytics"
            )

            await send_discord_files(
                image_paths=image_paths,
                content=message,
            )

            logger.info("Daily Discord digest complete")

        except Exception:
            logger.exception("Daily digest failed")


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
                daily_digest_loop(api, session),
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