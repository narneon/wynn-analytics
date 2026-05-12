import sqlite3
from pathlib import Path
from typing import Optional

from src.config.settings import LOCAL_DB_PATH
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


class SQLiteStore:
    def __init__(self, db_path: Path = LOCAL_DB_PATH):
        self.db_path = db_path

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        # Tracks players seen during the current hourly cycle
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_players_this_hour (
            hour_bucket TEXT NOT NULL,
            player_id TEXT NOT NULL,
            PRIMARY KEY (hour_bucket, player_id)
        )
        """)

        # Stores latest known lifetime raid totals
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_raid_totals (
            character_id TEXT PRIMARY KEY,
            player_id TEXT NOT NULL,
            player_name TEXT,
            nog_total INTEGER DEFAULT 0,
            nol_total INTEGER DEFAULT 0,
            tcc_total INTEGER DEFAULT 0,
            tna_total INTEGER DEFAULT 0,
            wtp_total INTEGER DEFAULT 0,
            last_seen_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_character_player
        ON character_raid_totals(player_id)
        """)

        self.conn.commit()

        logger.info("SQLite tables initialized")

    # -----------------------------
    # Seen player tracking
    # -----------------------------

    def add_seen_player(self, player_id: str, hour_bucket: str):
        cursor = self.conn.cursor()

        cursor.execute("""
                       INSERT
                       OR IGNORE INTO seen_players_this_hour (hour_bucket, player_id)
        VALUES (?, ?)
                       """, (hour_bucket, player_id))

        self.conn.commit()

    def get_seen_players_for_hour(self, hour_bucket: str) -> list[str]:
        cursor = self.conn.cursor()

        cursor.execute("""
                       SELECT player_id
                       FROM seen_players_this_hour
                       WHERE hour_bucket = ?
                       """, (hour_bucket,))

        return [row["player_id"] for row in cursor.fetchall()]

    def clear_seen_players_for_hour(self, hour_bucket: str):
        cursor = self.conn.cursor()

        cursor.execute("""
                       DELETE
                       FROM seen_players_this_hour
                       WHERE hour_bucket = ?
                       """, (hour_bucket,))

        self.conn.commit()

    # -----------------------------
    # Character totals tracking
    # -----------------------------

    def get_character_totals(self, character_id: str) -> Optional[dict]:
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT *
        FROM character_raid_totals
        WHERE character_id = ?
        """, (character_id,))

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    def upsert_character_totals(
        self,
        character_id: str,
        player_id: str,
        player_name: str,
        nog_total: int,
        nol_total: int,
        tcc_total: int,
        tna_total: int,
        wtp_total: int,
        last_seen_at: str,
    ):
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO character_raid_totals (
            character_id,
            player_id,
            player_name,
            nog_total,
            nol_total,
            tcc_total,
            tna_total,
            wtp_total,
            last_seen_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(character_id)
        DO UPDATE SET
            player_id = excluded.player_id,
            player_name = excluded.player_name,
            nog_total = excluded.nog_total,
            nol_total = excluded.nol_total,
            tcc_total = excluded.tcc_total,
            tna_total = excluded.tna_total,
            wtp_total = excluded.wtp_total,
            last_seen_at = excluded.last_seen_at
        """, (
            character_id,
            player_id,
            player_name,
            nog_total,
            nol_total,
            tcc_total,
            tna_total,
            wtp_total,
            last_seen_at,
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()
        logger.info("SQLite connection closed")