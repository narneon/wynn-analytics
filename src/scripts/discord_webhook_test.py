import asyncio
from pathlib import Path

from PIL import Image, ImageDraw

from src.config.settings import REPORT_OUTPUT_DIR
from src.reports.discord_client import send_discord_files


def create_test_image() -> Path:
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_path = REPORT_OUTPUT_DIR / "discord_webhook_test.png"

    image = Image.new("RGB", (900, 500), color=(24, 24, 28))
    draw = ImageDraw.Draw(image)

    draw.text(
        (50, 50),
        "Analytics Bot is not real",
        fill=(255, 255, 255),
    )

    draw.text(
        (50, 120),
        "6767676767",
        fill=(220, 220, 220),
    )

    image.save(image_path)

    return image_path


async def main():
    image_path = create_test_image()

    success = await send_discord_files(
        image_paths=[image_path],
        content="Discord webhook test",
    )

    print(f"Discord send success: {success}")
    print(f"Generated image: {image_path}")


if __name__ == "__main__":
    asyncio.run(main())