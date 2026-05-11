import asyncio
from datetime import datetime, timezone

import aiohttp

from src.api.wynn_api import WynnAPI
from src.collectors.archetype_classifier import classify_archetype
from src.config.settings import GLOBAL_CONCURRENCY
from src.database.bigquery_client import BigQueryClient
from src.database.sqlite_store import SQLiteStore
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


def compute_deltas(current: dict, previous: dict | None) -> dict:
    if previous is None:
        return {
            "nog_delta": 0,
            "nol_delta": 0,
            "tcc_delta": 0,
            "tna_delta": 0,
            "wtp_delta": 0,
        }

    return {
        "nog_delta": max(0, current["nog_total"] - previous["nog_total"]),
        "nol_delta": max(0, current["nol_total"] - previous["nol_total"]),
        "tcc_delta": max(0, current["tcc_total"] - previous["tcc_total"]),
        "tna_delta": max(0, current["tna_total"] - previous["tna_total"]),
        "wtp_delta": max(0, current["wtp_total"] - previous["wtp_total"]),
    }


def has_any_delta(deltas: dict) -> bool:
    return any(value > 0 for value in deltas.values())


async def process_player_raids(
    api: WynnAPI,
    session: aiohttp.ClientSession,
    sqlite_store: SQLiteStore,
    player_id: str,
    scan_timestamp: str,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    async with semaphore:
        try:
            payload = await api.fetch_player(session, player_id)

            if payload is None:
                logger.warning(f"Skipping player {player_id}: no payload")
                return []

            characters = api.parse_player_characters(payload)

            if not characters:
                return []

            rows_to_insert = []

            for character in characters:
                character_id = character["character_id"]

                previous_totals = sqlite_store.get_character_totals(character_id)
                deltas = compute_deltas(character, previous_totals)

                sqlite_store.upsert_character_totals(
                    character_id=character_id,
                    player_id=character["player_id"],
                    player_name=character["player_name"],
                    nog_total=character["nog_total"],
                    nol_total=character["nol_total"],
                    tcc_total=character["tcc_total"],
                    tna_total=character["tna_total"],
                    wtp_total=character["wtp_total"],
                    last_seen_at=scan_timestamp,
                )

                if previous_totals is None:
                    logger.info(f"Initialized baseline for character {character_id}")
                    continue

                if not has_any_delta(deltas):
                    continue

                removed_stats = character.get("removed_stats", [])

                can_fetch_atree = (
                        character.get("character_build_access") is not True
                        and "skillPoints" not in removed_stats
                )

                archetype = None

                if can_fetch_atree:
                    atree_payload = await api.fetch_atree(
                        session=session,
                        player_id=character["player_id"],
                        character_id=character_id,
                    )

                    archetype = classify_archetype(
                        atree_payload=atree_payload,
                        character_type=character["character_type"],
                    )

                row = {
                    "player_id": character["player_id"],
                    "character_id": character_id,
                    "player_name": character["player_name"],
                    "timestamp": scan_timestamp,
                    "archetype": archetype,

                    "str": character["str"],
                    "dex": character["dex"],
                    "int": character["int"],
                    "def": character["def"],
                    "agi": character["agi"],

                    **deltas,
                }

                rows_to_insert.append(row)

            return rows_to_insert

        except Exception:
            logger.exception(f"Unexpected raid processing failure for player {player_id}")
            return []


async def collect_raid_deltas_once(
    api: WynnAPI,
    session: aiohttp.ClientSession,
    sqlite_store: SQLiteStore,
    bq: BigQueryClient,
) -> bool:
    scan_timestamp = datetime.now(timezone.utc).isoformat()
    player_ids = sqlite_store.get_seen_players()

    if not player_ids:
        logger.info("No seen players to process for raid deltas")
        return True

    logger.info(
        f"Starting raid scan for {len(player_ids)} players "
        f"with concurrency={GLOBAL_CONCURRENCY}"
    )

    semaphore = asyncio.Semaphore(GLOBAL_CONCURRENCY)

    tasks = [
        process_player_raids(
            api=api,
            session=session,
            sqlite_store=sqlite_store,
            player_id=player_id,
            scan_timestamp=scan_timestamp,
            semaphore=semaphore,
        )
        for player_id in player_ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_rows = []

    for result in results:
        if isinstance(result, Exception):
            logger.exception("Raid task failed unexpectedly", exc_info=result)
            continue

        all_rows.extend(result)

    success = bq.insert_raid_rows(all_rows)

    if success:
        sqlite_store.clear_seen_players()
    else:
        logger.warning("Raid rows failed to insert; keeping seen players for retry")

    logger.info(
        f"Raid scan complete: "
        f"players_checked={len(player_ids)}, "
        f"delta_rows={len(all_rows)}, "
        f"bq_success={success}"
    )

    return success