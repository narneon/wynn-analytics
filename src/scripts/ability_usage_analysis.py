import asyncio
from datetime import datetime, timezone
from collections import defaultdict

from google.cloud import bigquery

from src.api.wynn_api import WynnAPI
from src.collectors.archetype_classifier import extract_selected_abilities
from src.config.settings import (
    GCP_PROJECT_ID,
    BQ_DATASET,
    BQ_RAID_TABLE,
    GLOBAL_CONCURRENCY,
)


TARGET_ARCHETYPE = "Boltslinger"
TARGET_ABILITY_ID = "inverseArsenal"

START_TIME = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
END_TIME = datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc)


def fetch_target_rows() -> list[dict]:
    client = bigquery.Client(project=GCP_PROJECT_ID)

    table = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_RAID_TABLE}"

    query = f"""
    SELECT DISTINCT
        player_id,
        character_id,
        archetype
    FROM `{table}`
    WHERE timestamp >= @start_time
      AND timestamp < @end_time
      AND archetype = @archetype
      AND character_id IS NOT NULL
      AND character_id != '__PLAYER_LEVEL__'
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", START_TIME),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", END_TIME),
            bigquery.ScalarQueryParameter("archetype", "STRING", TARGET_ARCHETYPE),
        ]
    )

    rows = list(client.query(query, job_config=job_config).result())

    return [dict(row) for row in rows]


async def character_has_ability(api, session, row: dict) -> tuple[str, bool] | None:
    player_id = row["player_id"]
    character_id = row["character_id"]

    atree_payload = await api.fetch_atree(
        session=session,
        player_id=player_id,
        character_id=character_id,
    )

    if not atree_payload:
        return None

    selected_abilities = extract_selected_abilities(atree_payload)

    return player_id, TARGET_ABILITY_ID in selected_abilities


async def main():
    rows = fetch_target_rows()

    print(f"Archetype: {TARGET_ARCHETYPE}")
    print(f"Ability ID: {TARGET_ABILITY_ID}")
    print(f"Window start: {START_TIME}")
    print(f"Window end:   {END_TIME}")
    print(f"Unique character rows to check: {len(rows)}")

    api = WynnAPI()

    semaphore = asyncio.Semaphore(GLOBAL_CONCURRENCY)

    async def worker(row):
        async with semaphore:
            return await character_has_ability(api, session, row)

    players_seen = {
        row["player_id"]
        for row in rows
    }

    players_with_ability = set()
    checked = 0
    failed = 0

    async with await api.create_session() as session:
        tasks = [
            asyncio.create_task(worker(row))
            for row in rows
        ]

        for task in asyncio.as_completed(tasks):
            result = await task
            checked += 1

            if checked % 200 == 0:
                print(f"Progress: {checked}/{len(rows)} checked")

            if result is None:
                failed += 1
                continue

            player_id, has_ability = result

            if has_ability:
                players_with_ability.add(player_id)

    total_players = len(players_seen)
    with_ability = len(players_with_ability)

    percentage = (
        with_ability / total_players * 100
        if total_players > 0
        else 0
    )

    print()
    print("=" * 60)
    print(f"Archetype: {TARGET_ARCHETYPE}")
    print(f"Ability:   {TARGET_ABILITY_ID}")
    print()
    print(f"Window: {START_TIME:%Y-%m-%d %H:%M UTC}")
    print(f"     -> {END_TIME:%Y-%m-%d %H:%M UTC}")
    print("=" * 60)

    print(f"Total unique players: {total_players}")
    print(f"Players with ability: {with_ability}")
    print(f"Failed/hidden atree checks: {failed}")
    print(f"Percentage: {percentage:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())