import argparse
import asyncio
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import bigquery

from src.api.wynn_api import WynnAPI
from src.collectors.archetype_classifier import extract_selected_abilities
from src.config.settings import (
    BQ_DATASET,
    BQ_RAID_TABLE,
    GCP_PROJECT_ID,
    GLOBAL_CONCURRENCY,
)


def parse_datetime(value: str) -> datetime:
    """
    Parse an ISO-8601 datetime.

    Examples:
        2026-09-01T17:30
        2026-09-01T17:30:00
        2026-09-01T17:30:00Z
        2026-09-01T17:30:00+00:00

    Datetimes without an explicit timezone are interpreted as UTC.
    """
    parsed = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def fetch_raider_characters(
    start_time: datetime,
    end_time: datetime,
) -> list[dict]:
    """
    Fetch distinct player/character pairs that recorded at least
    one positive raid delta during the requested timeframe.

    This only reads from BigQuery.
    """
    client = bigquery.Client(project=GCP_PROJECT_ID)

    hourly_table = (
        f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_RAID_TABLE}"
    )

    query = f"""
    SELECT DISTINCT
        player_id,
        character_id
    FROM `{hourly_table}`
    WHERE timestamp >= @start_time
      AND timestamp < @end_time
      AND (
          nog_delta > 0
          OR nol_delta > 0
          OR tcc_delta > 0
          OR tna_delta > 0
          OR wtp_delta > 0
      )
      AND player_id IS NOT NULL
      AND character_id IS NOT NULL
    ORDER BY player_id, character_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "start_time",
                "TIMESTAMP",
                start_time,
            ),
            bigquery.ScalarQueryParameter(
                "end_time",
                "TIMESTAMP",
                end_time,
            ),
        ]
    )

    rows = client.query(
        query,
        job_config=job_config,
    ).result()

    return [
        {
            "player_id": row["player_id"],
            "character_id": row["character_id"],
        }
        for row in rows
    ]


async def fetch_character_nodes(
    api: WynnAPI,
    session,
    player_id: str,
    character_id: str,
    semaphore: asyncio.Semaphore,
) -> set[str] | None:
    """
    Fetch the character's current ability tree and return all
    currently selected nodeNames.

    Returns None if the ability tree could not be fetched.
    """
    async with semaphore:
        payload = await api.fetch_atree(
            session=session,
            player_id=player_id,
            character_id=character_id,
        )

        if not payload:
            return None

        selected_abilities = extract_selected_abilities(
            payload
        )

        # Each node should count at most once per character.
        return set(selected_abilities)


async def collect_node_counts(
    raider_characters: list[dict],
) -> tuple[Counter, int]:
    """
    Fetch ability trees for all qualifying characters and count
    how many character trees contain each selected nodeName.
    """
    api = WynnAPI()

    semaphore = asyncio.Semaphore(
        GLOBAL_CONCURRENCY
    )

    node_counts = Counter()

    async with await api.create_session() as session:
        tasks = [
            fetch_character_nodes(
                api=api,
                session=session,
                player_id=row["player_id"],
                character_id=row["character_id"],
                semaphore=semaphore,
            )
            for row in raider_characters
        ]

        completed = 0
        successful = 0

        for task in asyncio.as_completed(tasks):
            nodes = await task
            completed += 1

            if nodes is not None:
                successful += 1
                node_counts.update(nodes)

            if completed % 100 == 0:
                print(
                    f"Processed "
                    f"{completed}/{len(tasks)} "
                    f"ability trees..."
                )

    return node_counts, successful


def write_csv(
    output_path: Path,
    node_counts: Counter,
) -> None:
    """
    Write:

        nodeName,uses
        bash,200
        uppercut,200
        ...
    """
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([
            "nodeName",
            "uses",
        ])

        for node_name, uses in node_counts.most_common():
            writer.writerow([
                node_name,
                uses,
            ])


async def main():
    parser = argparse.ArgumentParser(
        description=(
            "Count current selected ability-tree nodes among "
            "characters that raided during a specified timeframe."
        )
    )

    parser.add_argument(
        "--start",
        required=True,
        help=(
            "UTC start datetime. "
            "Example: 2026-09-14T17:30"
        ),
    )

    parser.add_argument(
        "--end",
        required=True,
        help=(
            "UTC end datetime. "
            "Example: 2026-09-21T17:31"
        ),
    )

    parser.add_argument(
        "--output",
        default="data/node_usage.csv",
        help=(
            "Output CSV path "
            "(default: data/node_usage.csv)"
        ),
    )

    args = parser.parse_args()

    start_time = parse_datetime(args.start)
    end_time = parse_datetime(args.end)

    if end_time <= start_time:
        raise ValueError(
            "end time must be after start time"
        )

    print("Node usage export")
    print("-----------------")
    print(f"Start:  {start_time}")
    print(f"End:    {end_time}")
    print(f"Output: {args.output}")

    print("\nQuerying qualifying raiders from BigQuery...")

    raider_characters = fetch_raider_characters(
        start_time=start_time,
        end_time=end_time,
    )

    unique_players = {
        row["player_id"]
        for row in raider_characters
    }

    print(
        f"Found {len(unique_players)} unique players "
        f"across {len(raider_characters)} "
        f"unique player/character pairs."
    )

    if not raider_characters:
        print("\nNo qualifying raiders found.")
        return

    print("\nFetching current ability trees...")

    node_counts, successful = await collect_node_counts(
        raider_characters
    )

    failed = len(raider_characters) - successful

    print()
    print(
        f"Successfully fetched: "
        f"{successful}/{len(raider_characters)}"
    )

    print(
        f"Failed/inaccessible:   {failed}"
    )

    print(
        f"Distinct nodeNames:    {len(node_counts)}"
    )

    output_path = Path(args.output)

    write_csv(
        output_path=output_path,
        node_counts=node_counts,
    )

    print(f"\nCSV written to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())