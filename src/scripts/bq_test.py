from datetime import datetime, timezone

from src.database.bigquery_client import BigQueryClient


def main():
    bq = BigQueryClient()

    test_row = {
        "player_id": "test_player",
        "character_id": "test_character",
        "player_name": "TestPlayer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "archetype": "Shadestepper",
        "str": 10,
        "dex": 20,
        "int": 30,
        "def": 40,
        "agi": 50,
        "nog_delta": 1,
        "nol_delta": 0,
        "tcc_delta": 0,
        "tna_delta": 0,
        "wtp_delta": 0,
    }

    success = bq.insert_raid_rows([test_row])

    print(f"Insert success: {success}")


if __name__ == "__main__":
    main()