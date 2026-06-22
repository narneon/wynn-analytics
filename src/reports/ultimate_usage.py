import asyncio

import aiohttp

from src.api.wynn_api import WynnAPI
from src.collectors.archetype_classifier import extract_selected_abilities
from src.config.settings import GLOBAL_CONCURRENCY
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


ARCHETYPE_ULTIMATE_NODES = {
    "Boltslinger": "boltslingerUlt",
    "Sharpshooter": "sharpshooterUlt",
    "Trapper": "trapperUlt",

    "Shadestepper": "shadestepperUlt",
    "Trickster": "tricksterUlt",
    "Acrobat": "acrobatUlt",

    "Arcanist": "arcanistUlt",
    "Riftwalker": "riftwalkerUlt",
    "Light Bender": "lightbenderUlt",

    "Summoner": "summonerUlt",
    "Ritualist": "ritualistUlt",
    "Acolyte": "acolyteUlt",

    "Fallen": "fallenUlt",
    "Battle Monk": "monkUlt",
    "Paladin": "paladinUlt",
}


async def character_has_archetype_ultimate(
    api: WynnAPI,
    session: aiohttp.ClientSession,
    player_id: str,
    character_id: str,
    archetype: str,
) -> bool:
    ultimate_node = ARCHETYPE_ULTIMATE_NODES.get(archetype)

    if not ultimate_node:
        return False

    atree_payload = await api.fetch_atree(
        session=session,
        player_id=player_id,
        character_id=character_id,
    )

    if not atree_payload:
        return False

    selected_abilities = extract_selected_abilities(atree_payload)

    return ultimate_node in selected_abilities


async def _check_ultimate_worker(
    api: WynnAPI,
    session: aiohttp.ClientSession,
    row: dict,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str, bool] | None:
    async with semaphore:
        player_id = row.get("player_id")
        character_id = row.get("character_id")
        raid = row.get("raid")
        archetype = row.get("archetype")

        if not player_id or not character_id or not raid or not archetype:
            return None

        has_ult = await character_has_archetype_ultimate(
            api=api,
            session=session,
            player_id=player_id,
            character_id=character_id,
            archetype=archetype,
        )

        return raid, archetype, has_ult


async def compute_ultimate_usage_counts(
    api: WynnAPI,
    session: aiohttp.ClientSession,
    raider_rows: list[dict],
) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], set[str]] = {}

    unique_rows_by_key = {}

    for row in raider_rows:
        key = (
            row.get("player_id"),
            row.get("character_id"),
            row.get("raid"),
            row.get("archetype"),
        )

        if None in key:
            continue

        unique_rows_by_key[key] = row

    unique_rows = list(unique_rows_by_key.values())

    logger.info(
        f"Checking ultimate usage for {len(unique_rows)} unique character/raid/archetype rows "
        f"with concurrency={GLOBAL_CONCURRENCY}"
    )

    semaphore = asyncio.Semaphore(GLOBAL_CONCURRENCY)

    tasks = [
        _check_ultimate_worker(
            api=api,
            session=session,
            row=row,
            semaphore=semaphore,
        )
        for row in unique_rows
    ]

    completed = 0

    for task in asyncio.as_completed(tasks):
        result = await task
        completed += 1

        if completed % 200 == 0:
            logger.info(
                f"Ultimate usage progress: {completed}/{len(unique_rows)} checked"
            )

        if result is None:
            continue

        raid, archetype, has_ult = result

        if has_ult:
            key = (raid, archetype)
            player_ids = counts.setdefault(key, set())
            player_ids.add(player_id)

    logger.info(f"Computed ultimate usage for {len(unique_rows)} unique rows")

    return {
        key: len(player_ids)
        for key, player_ids in counts.items()
    }