import datetime
from datetime import datetime as dt

from src.database.sqlite_store import SQLiteStore


def main():
    db = SQLiteStore()

    # Test seen players
    db.add_seen_player("player_123")
    db.add_seen_player("player_456")

    players = db.get_seen_players()

    print("Seen players:")
    print(players)

    # Test character totals upsert
    db.upsert_character_totals(
        character_id="char_abc",
        player_id="player_123",
        player_name="TestPlayer",
        nog_total=5,
        nol_total=2,
        tcc_total=1,
        tna_total=0,
        wtp_total=0,
        last_seen_at=dt.now(datetime.timezone.utc).isoformat(),
    )

    totals = db.get_character_totals("char_abc")

    print("\nCharacter totals:")
    print(totals)

    # Clear temporary table
    db.clear_seen_players()

    print("\nSeen players after clear:")
    print(db.get_seen_players())

    db.close()


if __name__ == "__main__":
    main()