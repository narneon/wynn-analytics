from pathlib import Path

import matplotlib.pyplot as plt

from src.config.settings import REPORT_OUTPUT_DIR
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


def generate_raid_digest_images(
    digest_rows: list[dict],
) -> list[Path]:
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated_paths = []

    for row in digest_rows:
        raid_name = row["raid_name"]

        image_path = (
            REPORT_OUTPUT_DIR
            / f"{row['raid']}_daily_digest.png"
        )

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.set_title(f"{raid_name} Daily Digest")

        ax.text(
            0.5,
            0.7,
            f"Completions: {row['completions']}",
            ha="center",
            fontsize=18,
        )

        ax.text(
            0.5,
            0.55,
            f"Unique Players: {row['unique_players']}",
            ha="center",
            fontsize=16,
        )

        ax.axis("off")

        plt.savefig(
            image_path,
            bbox_inches="tight",
            dpi=150,
        )

        plt.close(fig)

        generated_paths.append(image_path)

        logger.info(f"Generated digest image: {image_path}")

    return generated_paths