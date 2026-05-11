import asyncio

from src.api.wynn_api import WynnAPI
from src.collectors.archetype_classifier import (
    classify_archetype,
    extract_selected_abilities,
)
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


TEST_PLAYERS = [
    "Badpoopy",
    "e95f089e-8d79-4a5d-858d-cebb1fdc5ee1",
    "Warze",
    "MFLR5",
    "EscimoCandy",
]


async def main():
    api = WynnAPI()

    async with await api.create_session() as session:
        for player_id in TEST_PLAYERS:
            print("=" * 80)
            print(f"Testing player: {player_id}")

            player_payload = await api.fetch_player(session, player_id)

            if not player_payload:
                print("Failed to fetch full player payload")
                continue

            restrictions = player_payload.get("restrictions", {})
            print("Restrictions:", restrictions)

            characters = api.parse_player_characters(player_payload)

            print(f"Parsed 119+ characters: {len(characters)}")

            for character in characters:
                character_id = character["character_id"]
                character_type = character["character_type"]

                print("-" * 60)
                print(f"Character ID: {character_id}")
                print(f"Class: {character_type}")

                character_build_access = restrictions.get("characterBuildAccess")

                if character_build_access is True:
                    print("Skipping atree fetch: characterBuildAccess is restricted")
                    continue

                atree_payload = await api.fetch_atree(
                    session=session,
                    player_id=player_id,
                    character_id=character_id,
                )

                if not atree_payload:
                    print("No atree payload / hidden build / failed request")
                    print("Archetype: None")
                    continue

                selected_abilities = extract_selected_abilities(atree_payload)

                archetype = classify_archetype(
                    atree_payload=atree_payload,
                    character_type=character_type,
                )

                print(f"Selected ability count: {len(selected_abilities)}")
                print(f"First 15 abilities: {sorted(selected_abilities)[:15]}")
                print(f"Archetype: {archetype}")


if __name__ == "__main__":
    asyncio.run(main())