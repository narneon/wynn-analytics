import asyncio
from pprint import pprint

from src.api.wynn_api import WynnAPI
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


TEST_PLAYERS = [
    "MFLR5",
    "Twigbones",
    "EscimoCandy",
    "Warze"
]


async def test_player(api: WynnAPI, session, player_id: str) -> dict:
    print("=" * 80)
    print(f"Testing player: {player_id}\n")

    player_payload = await api.fetch_player(session, player_id)

    if player_payload is None:
        print("Player endpoint failed or returned no data\n")
        return {
            "player_id": player_id,
            "success": False,
            "character_count": 0,
            "characters": [],
        }

    parsed_characters = api.parse_player_characters(player_payload)

    print(f"Parsed level 119+ characters: {len(parsed_characters)}\n")

    for character in parsed_characters:
        print("-" * 60)
        print(f"Character ID: {character['character_id']}")
        print(f"Class: {character['character_type']}")

        print("Raid totals:")
        print({
            "nog": character["nog_total"],
            "nol": character["nol_total"],
            "tcc": character["tcc_total"],
            "tna": character["tna_total"],
            "wtp": character["wtp_total"],
        })

        print("Skill points:")
        print({
            "str": character["str"],
            "dex": character["dex"],
            "int": character["int"],
            "def": character["def"],
            "agi": character["agi"],
        })

    return {
        "player_id": player_id,
        "success": True,
        "character_count": len(parsed_characters),
        "characters": parsed_characters,
    }


async def main():
    api = WynnAPI()
    results = []

    async with await api.create_session() as session:
        print("Testing online player endpoint...\n")

        online_payload = await api.fetch_online_players(session)

        if online_payload is None:
            print("Online player endpoint failed\n")
        else:
            total, players = api.parse_online_players(online_payload)
            print(f"Online total: {total}")
            print(f"Parsed UUID count: {len(players)}")
            print(f"First 5 UUIDs: {players[:5]}\n")

        for player_id in TEST_PLAYERS:
            result = await test_player(api, session, player_id)
            results.append(result)

    print("\n" + "=" * 80)
    print("Summary:\n")

    for result in results:
        print(
            f"{result['player_id']}: "
            f"success={result['success']}, "
            f"119+ characters={result['character_count']}"
        )

    print("\nFull parsed result object:\n")
    pprint(results)


if __name__ == "__main__":
    asyncio.run(main())