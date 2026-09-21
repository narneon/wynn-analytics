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

    print("Weekly digest integration test")
    print("------------------------------")
    print(f"Digest date: {window['digest_date']}")
    print(f"Start:       {window['start_time_utc']}")
    print(f"End:         {window['end_time_utc']}")

    rows = digest_service.fetch_period_digest_rows(window)

    print(f"\nFetched {len(rows)} period rows.")

    if not rows:
        raise RuntimeError("Weekly period query returned no rows")

    # Validate period data before generating/sending anything.
    known_rows = [
        row
        for row in rows
        if row["archetype"] != "Unknown"
    ]

    assert all(
        row["completions"] >= 0
        for row in rows
    )

    assert all(
        row["unique_players"] >= 0
        for row in rows
    )

    assert all(
        row["ult_uses"] is None
        for row in rows
    )

    assert all(
        row["ult_usage_pct"] is not None
        for row in known_rows
    )

    assert all(
        0 <= row["ult_usage_pct"] <= 100
        for row in known_rows
    )

    print("Period data validation passed.")

    image_paths = generate_raid_digest_images(
        rows,
        period_label="Weekly",
    )

    if len(image_paths) != 5:
        raise RuntimeError(
            f"Expected 5 weekly images, got {len(image_paths)}"
        )

    print("\nGenerated weekly images:")

    for path in image_paths:
        print(f"  {path}")

    print("\nSending weekly digest to Discord...")

    discord_success = await send_discord_files(
        image_paths=image_paths,
        content="Weekly Wynncraft Raid Report Test",
    )

    if not discord_success:
        raise RuntimeError("Discord send failed")

    print("\nWeekly digest successfully sent to Discord.")
    print("Weekly digest integration test passed.")


if __name__ == "__main__":
    asyncio.run(main())