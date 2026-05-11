import asyncio
import time

from src.api.wynn_api import WynnAPI
from src.database.bigquery_client import BigQueryClient
from src.database.sqlite_store import SQLiteStore
from src.collectors.raid_tracker import collect_raid_deltas_once


async def main():
    api = WynnAPI()
    db = SQLiteStore()
    bq = BigQueryClient()

    async with await api.create_session() as session:
        # Make sure SQLite has players to scan.
        test_players = [
            "MFLR5",
            "Twigbones",
            "EscimoCandy",
            "Badpoopy"
        ]

        for player in test_players:
            db.add_seen_player(player)

        print("First pass: initializes baselines, should insert 0 raid rows.")
        success_1 = await collect_raid_deltas_once(api, session, db, bq)
        print(f"First pass success: {success_1}")
        # time.sleep(600)

        for player in test_players:
            db.add_seen_player(player)

        print("\nSecond pass: should usually insert 0 rows unless someone raided between passes.")
        success_2 = await collect_raid_deltas_once(api, session, db, bq)
        print(f"Second pass success: {success_2}")

    print("\nRemaining seen players after scan:")
    print(db.get_seen_players())

    db.close()


if __name__ == "__main__":
    asyncio.run(main())