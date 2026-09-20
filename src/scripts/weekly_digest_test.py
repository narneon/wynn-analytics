import asyncio

from src.reports.chart_images import generate_raid_digest_images
from src.reports.daily_digest import (
    DailyDigestService,
    get_weekly_window,
)
from src.reports.discord_client import send_discord_files


async def main():
    digest_service = DailyDigestService()

    window = get_weekly_window()

    print("Weekly digest window:")
    print(f"  digest_date: {window['digest_date']}")
    print(f"  start_time_utc: {window['start_time_utc']}")
    print(f"  end_time_utc: {window['end_time_utc']}")

    digest_rows = digest_service.fetch_daily_digest_rows(
        window=window,
    )

    print(f"\nFetched weekly digest rows: {len(digest_rows)}")

    for row in digest_rows[:10]:
        print(row)

    missing_ult_rows = [
        row
        for row in digest_rows
        if row.get("ult_uses") is None
    ]

    if missing_ult_rows:
        print(
            f"\nWarning: {len(missing_ult_rows)} rows have "
            "ult_uses=None"
        )

        for row in missing_ult_rows[:10]:
            print(
                row.get("raid"),
                row.get("archetype"),
                row.get("digest_date"),
            )

    image_paths = generate_raid_digest_images(
        digest_rows,
        period_label="Weekly",
    )

    print("\nGenerated weekly images:")

    for path in image_paths:
        print(path)

    discord_success = await send_discord_files(
        image_paths=image_paths,
        content="Weekly Wynncraft Raid Report Test",
    )

    print(f"\nDiscord send success: {discord_success}")


if __name__ == "__main__":
    asyncio.run(main())