from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from src.config.settings import (
    GCP_PROJECT_ID,
    BQ_DATASET,
    BQ_RAID_TABLE,
    BQ_ONLINE_TABLE,
    DRY_RUN,
)
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client(project=GCP_PROJECT_ID)

        self.raid_table_id = (
            f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_RAID_TABLE}"
        )

        self.online_table_id = (
            f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_ONLINE_TABLE}"
        )

        logger.info("BigQuery client initialized")

    # -----------------------------------
    # Hourly raid delta inserts
    # -----------------------------------

    def insert_raid_rows(self, rows: list[dict]) -> bool:
        if DRY_RUN:
            logger.info(f"DRY_RUN: skipped raid row insert count={len(rows)}")
            return True

        if not rows:
            logger.info("No raid rows to insert")
            return True

        try:
            errors = self.client.insert_rows_json(
                self.raid_table_id,
                rows,
            )

            if errors:
                logger.error(f"BigQuery raid insert errors: {errors}")
                return False

            logger.info(f"Inserted {len(rows)} raid rows")

            return True

        except GoogleCloudError:
            logger.exception("BigQuery raid insert failed")
            return False

    # -----------------------------------
    # Online player count inserts
    # -----------------------------------

    def insert_online_player_row(self, row: dict) -> bool:
        if DRY_RUN:
            logger.info(f"DRY_RUN: skipped online player insert: {row}")
            return True

        try:
            errors = self.client.insert_rows_json(
                self.online_table_id,
                [row],
            )

            if errors:
                logger.error(f"BigQuery online insert errors: {errors}")
                return False

            logger.info("Inserted online player count row")

            return True

        except GoogleCloudError:
            logger.exception("BigQuery online insert failed")
            return False