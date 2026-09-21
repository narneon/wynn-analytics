from pathlib import Path

import aiohttp

from src.config.settings import DISCORD_WEBHOOK_URL
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


async def send_discord_files(
    image_paths: list[Path],
    content: str = "",
    thread_id: str | None = None,
    webhook_url: str = DISCORD_WEBHOOK_URL,
) -> bool:
    if not image_paths:
        logger.warning("No Discord files to send")
        return False

    form = aiohttp.FormData()

    if content:
        form.add_field("content", content)

    open_files = []

    try:
        for index, image_path in enumerate(image_paths):
            file_obj = image_path.open("rb")
            open_files.append(file_obj)

            form.add_field(
                name=f"files[{index}]",
                value=file_obj,
                filename=image_path.name,
                content_type="image/png",
            )

        params = {}

        if thread_id is not None:
            params["thread_id"] = thread_id

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                params=params,
                data=form,
            ) as response:
                if response.status not in {200, 204}:
                    text = await response.text()
                    logger.error(
                        f"Discord webhook failed: status={response.status}, body={text[:500]}"
                    )
                    return False

                logger.info(f"Sent {len(image_paths)} files to Discord")
                return True

    finally:
        for file_obj in open_files:
            file_obj.close()