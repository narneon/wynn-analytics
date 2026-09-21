import argparse
from datetime import date

from src.reports.chart_images import generate_raid_digest_images
from src.reports.daily_digest import (
    DailyDigestService,
    get_period_window,
)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected YYYY-MM-DD."
        ) from exc


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Wynncraft raid report for an arbitrary date range."
    )

    parser.add_argument(
        "--start",
        required=True,
        type=parse_date,
        help="First reporting date, inclusive (YYYY-MM-DD).",
    )

    parser.add_argument(
        "--end",
        required=True,
        type=parse_date,
        help="Last reporting date, inclusive (YYYY-MM-DD).",
    )

    parser.add_argument(
        "--label",
        default="Period",
        help="Label displayed on the generated report. Default: Period",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    window = get_period_window(
        start_date=args.start,
        end_date=args.end,
    )

    print("Generating period digest")
    print("------------------------")
    print(f"Start date: {args.start}")
    print(f"End date:   {args.end}")
    print(f"Label:      {args.label}")
    print(f"Window:     {window['start_time_utc']} -> {window['end_time_utc']}")

    digest_service = DailyDigestService()

    rows = digest_service.fetch_period_digest_rows(window)

    if not rows:
        raise RuntimeError(
            "No raid data was found for the requested period."
        )

    print(f"\nFetched {len(rows)} digest rows.")

    image_paths = generate_raid_digest_images(
        rows,
        period_label=args.label,
    )

    print("\nGenerated images:")

    for path in image_paths:
        print(f"  {path}")

    print("\nPeriod digest complete.")


if __name__ == "__main__":
    main()