import asyncio

from src.api.wynn_api import WynnAPI
from src.database.bigquery_client import BigQueryClient
from src.database.sqlite_store import SQLiteStore
from src.collectors.online_players import collect_online_players_once


async def main():
    api = WynnAPI()
    db = SQLiteStore()
    bq = BigQueryClient()

    async with await api.create_session() as session:
        success = await collect_online_players_once(
            api=api,
            session=session,
            sqlite_store=db,
            bq=bq,
        )

    print(f"Online player collection success: {success}")
    print(f"Unique players in SQLite this hour: {len(db.get_seen_players())}")

    db.close()


if __name__ == "__main__":
    asyncio.run(main())