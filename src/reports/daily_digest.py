from datetime import datetime, time, timedelta, timezone

from google.cloud import bigquery

from src.config.settings import (
    GCP_PROJECT_ID,
    BQ_DATASET,
    BQ_RAID_TABLE,
    BQ_DAILY_TABLE,
    DAILY_DIGEST_HOUR_UTC,
    DAILY_DIGEST_MINUTE_UTC,
)
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


RAIDS = [
    {"raid": "nog", "raid_name": "Nest of the Grootslangs", "delta_column": "nog_delta"},
    {"raid": "nol", "raid_name": "Orphion's Nexus of Light", "delta_column": "nol_delta"},
    {"raid": "tcc", "raid_name": "The Canyon Colossus", "delta_column": "tcc_delta"},
    {"raid": "tna", "raid_name": "The Nameless Anomaly", "delta_column": "tna_delta"},
    {"raid": "wtp", "raid_name": "The Wartorn Palace", "delta_column": "wtp_delta"},
]


def get_daily_digest_window(now: datetime | None = None) -> dict:
    if now is None:
        now = datetime.now(timezone.utc)

    digest_end = datetime.combine(
        now.date(),
        time(
            hour=DAILY_DIGEST_HOUR_UTC,
            minute=DAILY_DIGEST_MINUTE_UTC + 1,
        ),
        tzinfo=timezone.utc,
    )

    if now < digest_end:
        digest_end -= timedelta(days=1)

    digest_start = digest_end - timedelta(days=1, minutes=1)

    return {
        "digest_date": digest_end.date(),
        "start_time_utc": digest_start,
        "end_time_utc": digest_end,
    }


class DailyDigestService:
    def __init__(self):
        self.client = bigquery.Client(project=GCP_PROJECT_ID)
        self.hourly_table = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_RAID_TABLE}"
        self.digest_table = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_DAILY_TABLE}"

    def fetch_daily_digest_rows(self) -> list[dict]:
        window = get_daily_digest_window()
        all_rows = []

        for raid_config in RAIDS:
            all_rows.extend(
                self._fetch_raid_archetype_rows(
                    raid=raid_config["raid"],
                    delta_column=raid_config["delta_column"],
                    digest_date=window["digest_date"],
                    start_time_utc=window["start_time_utc"],
                    end_time_utc=window["end_time_utc"],
                )
            )

        logger.info(
            f"Fetched {len(all_rows)} daily digest rows "
            f"for digest_date={window['digest_date']}"
        )
        return all_rows

    def _fetch_raid_archetype_rows(
        self,
        raid: str,
        delta_column: str,
        digest_date,
        start_time_utc: datetime,
        end_time_utc: datetime,
    ) -> list[dict]:
        query = f"""
        SELECT
            @digest_date AS digest_date,
            @raid AS raid,
            COALESCE(archetype, 'Unknown') AS archetype,

            SUM({delta_column}) AS completions,
            COUNT(DISTINCT player_id) AS unique_players,

            AVG(str) AS avg_str,
            AVG(dex) AS avg_dex,
            AVG(int) AS avg_int,
            AVG(def) AS avg_def,
            AVG(agi) AS avg_agi,

            CAST(NULL AS INT64) AS ult_uses,

            CURRENT_TIMESTAMP() AS created_at
        FROM `{self.hourly_table}`
        WHERE timestamp >= @start_time
          AND timestamp < @end_time
          AND {delta_column} > 0
        GROUP BY archetype
        ORDER BY completions DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("digest_date", "DATE", digest_date),
                bigquery.ScalarQueryParameter("raid", "STRING", raid),
                bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time_utc),
                bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time_utc),
            ]
        )

        results = []
        for row in self.client.query(query, job_config=job_config).result():
            results.append({
                "digest_date": row["digest_date"].isoformat(),
                "raid": row["raid"],
                "archetype": row["archetype"],
                "completions": int(row["completions"] or 0),
                "unique_players": int(row["unique_players"] or 0),
                "avg_str": row["avg_str"],
                "avg_dex": row["avg_dex"],
                "avg_int": row["avg_int"],
                "avg_def": row["avg_def"],
                "avg_agi": row["avg_agi"],
                "ult_uses": row["ult_uses"],
                "created_at": row["created_at"].isoformat(),
            })

        return results

    def fetch_daily_raider_rows(self) -> list[dict]:
        window = get_daily_digest_window()
        union_queries = []

        for raid_config in RAIDS:
            union_queries.append(f"""
            SELECT
                player_id,
                character_id,
                @raid_{raid_config["raid"]} AS raid,
                COALESCE(archetype, 'Unknown') AS archetype
            FROM `{self.hourly_table}`
            WHERE timestamp >= @start_time
              AND timestamp < @end_time
              AND {raid_config["delta_column"]} > 0
              AND archetype IS NOT NULL
              AND archetype != 'Unknown'
            """)

        query = "\nUNION DISTINCT\n".join(union_queries)

        query_parameters = [
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", window["start_time_utc"]),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", window["end_time_utc"]),
        ]

        for raid_config in RAIDS:
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    f"raid_{raid_config['raid']}",
                    "STRING",
                    raid_config["raid"],
                )
            )

        job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)

        rows = list(self.client.query(query, job_config=job_config).result())
        return [dict(row) for row in rows]

    def insert_daily_digest_rows(self, rows: list[dict]) -> bool:
        if not rows:
            logger.warning("No daily digest rows to insert")
            return True

        errors = self.client.insert_rows_json(self.digest_table, rows)

        if errors:
            logger.error(f"Daily digest BigQuery insert errors: {errors}")
            return False

        logger.info(f"Inserted {len(rows)} rows into {self.digest_table}")
        return True