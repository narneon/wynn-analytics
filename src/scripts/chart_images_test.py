from src.reports.chart_images import build_dashboard_data


def make_row(
    archetype,
    unique_players,
    ult_uses,
    ult_usage_pct=None,
):
    row = {
        "raid": "tna",
        "archetype": archetype,
        "completions": 100,
        "unique_players": unique_players,
        "avg_str": 20,
        "avg_dex": 30,
        "avg_int": 40,
        "avg_def": 50,
        "avg_agi": 60,
        "ult_uses": ult_uses,
        "digest_date": "2026-09-21",
    }

    if ult_usage_pct is not None:
        row["ult_usage_pct"] = ult_usage_pct

    return row


def main():
    rows = [
        # Existing daily behavior:
        # 40 / 100 = 40%
        make_row(
            archetype="Boltslinger",
            unique_players=100,
            ult_uses=40,
        ),

        # Period behavior:
        # Precomputed 72.5% should override 10 / 200 = 5%
        make_row(
            archetype="Trapper",
            unique_players=200,
            ult_uses=10,
            ult_usage_pct=72.5,
        ),

        # Unknown should still be excluded from ultimate usage.
        make_row(
            archetype="Unknown",
            unique_players=50,
            ult_uses=50,
            ult_usage_pct=100.0,
        ),
    ]

    dashboard_data = build_dashboard_data(
        raid="tna",
        digest_rows=rows,
    )

    ultimate_usage = dashboard_data["ultimate_usage"]

    print("Ultimate usage:")
    print(ultimate_usage)

    assert ultimate_usage["Boltslinger"] == 40.0
    assert ultimate_usage["Trapper"] == 72.5
    assert "Unknown" not in ultimate_usage

    print("\nAll chart image tests passed.")


if __name__ == "__main__":
    main()