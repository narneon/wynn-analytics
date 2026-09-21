from datetime import date

from src.reports.chart_images import generate_raid_digest_images
from src.reports.daily_digest import (
    DailyDigestService,
    get_period_window,
)


def main():
    start_date = date(2026, 9, 1)
    end_date = date(2026, 9, 7)

    window = get_period_window(
        start_date=start_date,
        end_date=end_date,
    )

    print("Period digest test")
    print("------------------")
    print(f"Start date:  {start_date}")
    print(f"End date:    {end_date}")
    print(f"Digest date: {window['digest_date']}")
    print(f"Start:       {window['start_time_utc']}")
    print(f"End:         {window['end_time_utc']}")

    digest_service = DailyDigestService()

    rows = digest_service.fetch_period_digest_rows(window)

    print(f"\nFetched {len(rows)} period rows.")

    if not rows:
        raise RuntimeError("Period query returned no rows")

    print("\nPeriod rows:")
    print("------------")

    for row in rows:
        print(
            f"{row['raid']:>3} | "
            f"{row['archetype']:<15} | "
            f"completions={row['completions']:<6} | "
            f"players={row['unique_players']:<5} | "
            f"ult={row['ult_usage_pct']}"
        )

    known_rows = [
        row
        for row in rows
        if row["archetype"] != "Unknown"
    ]

    assert all(
        row["ult_usage_pct"] is not None
        for row in known_rows
    )

    assert all(
        0 <= row["ult_usage_pct"] <= 100
        for row in known_rows
    )

    image_paths = generate_raid_digest_images(
        rows,
        period_label="Period Test",
    )

    print("\nGenerated images:")
    print("-----------------")

    for path in image_paths:
        print(path)

    assert len(image_paths) == 5

    print("\nAll period digest tests passed.")


if __name__ == "__main__":
    main()