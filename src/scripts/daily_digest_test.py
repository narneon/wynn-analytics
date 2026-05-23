import asyncio
from collections import defaultdict

from src.api.wynn_api import WynnAPI
from src.reports.chart_images import generate_raid_digest_images
from src.reports.daily_digest import (
    DailyDigestService,
    RAIDS,
    get_daily_digest_window,
)
from src.reports.discord_client import send_discord_files
from src.reports.ultimate_usage import compute_ultimate_usage_counts

from datetime import datetime, timezone

async def main():
    digest_service = DailyDigestService()
    api = WynnAPI()

    window = get_daily_digest_window()

    print("Digest window:")
    print(f"  digest_date: {window['digest_date']}")
    print(f"  start_time_utc: {window['start_time_utc']}")
    print(f"  end_time_utc: {window['end_time_utc']}")

    digest_rows = digest_service.fetch_daily_digest_rows()

    print(f"\nFetched digest rows: {len(digest_rows)}")

    for row in digest_rows[:10]:
        print(row)

    raider_rows = digest_service.fetch_daily_raider_rows()

    print(f"\nFetched raider rows for ult checks: {len(raider_rows)}")

    async with await api.create_session() as session:
        ult_counts = await compute_ultimate_usage_counts(
            api=api,
            session=session,
            raider_rows=raider_rows,
        )

    print("\nUltimate counts:")
    print(ult_counts)

    for row in digest_rows:
        key = (row["raid"], row["archetype"])
        row["ult_uses"] = ult_counts.get(key, 0)

    insert_success = digest_service.insert_daily_digest_rows(digest_rows)

    print(f"\nDaily digest BigQuery insert success: {insert_success}")

    grouped = defaultdict(list)

    for row in digest_rows:
        grouped[row["raid"]].append(row)

    image_paths = generate_raid_digest_images(digest_rows)

    print("\nGenerated images:")

    for path in image_paths:
        print(path)

    current_date = datetime.now(timezone.utc).strftime("%m/%d/%Y")

    message = (
        "TEST MESSAGE\n"
        "Daily Wynncraft Raid Report\n"
        f"Date: {current_date}\n"
        "Wynn Analytics Link: <https://discord.gg/xxxQ7PJB4k>"
    )

    discord_success = await send_discord_files(
        image_paths=image_paths,
        content=message,
    )

    print(f"\nDiscord send success: {discord_success}")


if __name__ == "__main__":
    asyncio.run(main())