from datetime import datetime, timezone

import aiohttp

from src.api.wynn_api import WynnAPI
from src.database.sqlite_store import SQLiteStore
from src.database.bigquery_client import BigQueryClient
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


async def collect_online_players_once(
    api: WynnAPI,
    session: aiohttp.ClientSession,
    sqlite_store: SQLiteStore,
    bq: BigQueryClient,
) -> bool:
    payload = await api.fetch_online_players(session)

    if payload is None:
        logger.warning("Online player collection skipped: API returned no payload")
        return False

    online_total, player_ids = api.parse_online_players(payload)

    timestamp = datetime.now(timezone.utc).isoformat()

    for player_id in player_ids:
        sqlite_store.add_seen_player(player_id)

    row = {
        "timestamp": timestamp,
        "player_count": online_total,
    }

    success = bq.insert_online_player_row(row)

    logger.info(
        f"Online collection complete: "
        f"online_total={online_total}, "
        f"bq_success={success}"
    )

    return success