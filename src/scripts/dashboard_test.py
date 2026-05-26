from pathlib import Path
import random
import math

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pip._internal.resolution.resolvelib import candidates

OUTPUT_DIR = Path("data/reports")
OUTPUT_PATH = OUTPUT_DIR / "sample_digest.png"

RAID = 'wtp'

ICON_PATH = Path(f"assets/{RAID}_icon.png")

W, H = 1600, 1875

RAID_COLORS = {
    'nog': (69, 105, 39),
    'nol': (212, 177, 72),
    'tcc': (118, 149, 166),
    'tna': (58, 39, 102),
    'wtp': (79, 3, 8),
}


COLORS = {
    "bg": (8, 14, 13),
    "bg2": (12, 22, 18),
    "gold_dim": (93, 82, 37),
    "title_text": (212, 212, 212),
    "accent": RAID_COLORS[RAID],
    "text": (230, 211, 157),
    "muted": (170, 154, 103),

    "Warrior": (255, 123, 114),
    "Mage": (121, 192, 255),
    "Assassin": (255, 166, 87),
    "Archer": (86, 211, 100),
    "Shaman": (210, 168, 255),
}

CLASS_LIST = [
    "Warrior",
    "Mage",
    "Assassin",
    "Archer",
    "Shaman"
]

ARCHETYPE_HEX = {
    "Boltslinger": "#ffcc00",
    "Trapper": "#006400",
    "Sharpshooter": "#ff00ff",
    "Riftwalker": "#add8e6",
    "Lightbender": "#808080",
    "Arcanist": "#8a2be2",
    "Shadestepper": "#0f766e",
    "Trickster": "#4b0082",
    "Acrobat": "#c0c0c0",
    "Fallen": "#ff0000",
    "Battlemonk": "#fffd8d",
    "Paladin": "#00008b",
    "Summoner": "#ffa500",
    "Ritualist": "#90ee90",
    "Acolyte": "#ff4500",
}

ARCHETYPE_LIST = [
    "Boltslinger",
    "Trapper",
    "Sharpshooter",
    "Riftwalker",
    "Lightbender",
    "Arcanist",
    "Shadestepper",
    "Trickster",
    "Acrobat",
    "Fallen",
    "Battlemonk",
    "Paladin",
    "Summoner",
    "Ritualist",
    "Acolyte",
]


def hextrgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def pastels(color: tuple[int, int, int], mix: float = 0.52) -> tuple[int, int, int]:
    return tuple(int(component + (255 - component) * mix) for component in color)


ARCHETYPE_PCOLORS = {
    archetype: hextrgb(color_hex)
    for archetype, color_hex in ARCHETYPE_HEX.items()
}

ARCHETYPE_CCOLORS = {
    archetype: pastels(hextrgb(color_hex))
    for archetype, color_hex in ARCHETYPE_HEX.items()
}

RADAR_FIXED = ["Archer", "Mage", "Assassin", "Warrior", "Shaman"]

RADAR_ARCHCLASS = {
    "Archer": ["Boltslinger", "Trapper", "Sharpshooter"],
    "Mage": ["Riftwalker", "Lightbender", "Arcanist"],
    "Assassin": ["Shadestepper", "Trickster", "Acrobat"],
    "Warrior": ["Fallen", "Battlemonk", "Paladin"],
    "Shaman": ["Summoner", "Ritualist", "Acolyte"],
}

def load_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf",
    ]
    # candidates = ["data/assets/wynn-wynncraft.ttf"]
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


FONT_TITLE = load_font(76, bold=True)
FONT_SUBTITLE = load_font(34)
FONT_SECTION = load_font(32, bold=True)
FONT_BODY = load_font(24)
FONT_SMALL = load_font(18, bold=True)
FONT_SMALLER = load_font(15, bold=True)

def add_noise_background(img: Image.Image):
    noise = Image.new("RGB", img.size)
    px = noise.load()

    for y in range(img.height):
        for x in range(img.width):
            base = random.randint(0, 22)
            px[x, y] = (
                max(0, COLORS["bg"][0] + base),
                max(0, COLORS["bg"][1] + base),
                max(0, COLORS["bg"][2] + base),
            )

    noise = noise.filter(ImageFilter.GaussianBlur(2))
    img.paste(noise)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 95))
    img.alpha_composite(overlay)


def draw_outer_border(draw: ImageDraw.ImageDraw):
    margin = 22

    draw.rectangle(
        [margin, margin, W - margin, H - margin],
        outline=COLORS["accent"],
        width=3,
    )

    draw.rectangle(
        [margin + 10, margin + 10, W - margin - 10, H - margin - 10],
        outline=COLORS["gold_dim"],
        width=2,
    )

    # Corner ornaments
    for sx, sy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
    # for sx, sy in [(-1, 1), (1, -1), (-1, -1)]:
        cx = margin + 28 if sx == 1 else W - margin - 28
        cy = margin + 28 if sy == 1 else H - margin - 28

        draw.line([(cx, cy), (cx + sx * 90, cy)], fill=COLORS["accent"], width=3)
        draw.line([(cx, cy), (cx, cy + sy * 90)], fill=COLORS["accent"], width=3)

        draw.line(
            [(cx + sx * 20, cy + sy * 20), (cx + sx * 70, cy + sy * 20)],
            fill=COLORS["gold_dim"],
            width=2,
        )
        draw.line(
            [(cx + sx * 20, cy + sy * 20), (cx + sx * 20, cy + sy * 70)],
            fill=COLORS["gold_dim"],
            width=2,
        )


def draw_centered_text(draw, x1, x2, text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = ((x2 - x1) - (bbox[2] - bbox[0])) // 2 + x1
    draw.text((x if x > 0 else 0, y), text, font=font, fill=fill)


def draw_divider(draw, y):
    x1, x2 = 60, W - 60
    draw.line([(x1, y), (W // 2 - 25, y)], fill=COLORS["gold_dim"], width=2)
    draw.line([(W // 2 + 25, y), (x2, y)], fill=COLORS["gold_dim"], width=2)

    diamond = [
        (W // 2, y - 9),
        (W // 2 + 9, y),
        (W // 2, y + 9),
        (W // 2 - 9, y),
    ]
    draw.polygon(diamond, outline=COLORS["gold_dim"], fill=COLORS["accent"], width=2)


def draw_panel(draw, box, title=None):
    x1, y1, x2, y2 = box

    draw.rectangle(box, outline=COLORS["gold_dim"], width=2)

    inner = [x1 + 6, y1 + 6, x2 - 6, y2 - 6]
    draw.rectangle(inner, outline=COLORS["accent"], width=2)

    if title:
        bbox = draw.textbbox((0, 0), title, font=FONT_SECTION)
        text_w = bbox[2] - bbox[0]

        draw.text(
            (
                (x1 + x2) / 2 - text_w / 2,
                y1 + 12,
            ),
            title,
            font=FONT_SECTION,
            fill=COLORS["title_text"],
        )


def draw_pie(draw, center, radius, values, labels, colors, legend_x=None, legend_y=None):
    total = sum(values)
    start = -90

    for value, color in zip(values, colors):
        angle = 360 * value / total if total else 0

        end = start + angle

        draw.pieslice(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            start,
            end,
            fill=color,
            outline=COLORS["gold_dim"],
            width=2,
        )

        start = end

    start = -90

    for value, color in zip(values, colors):
        angle = 360 * value / total if total else 0

        end = start + angle

        # Percentage label
        pct = value / total * 100 if total else 0
        pct_text = f"{pct:.1f}%"

        mid_angle = math.radians((start + end) / 2)

        text_radius = radius * 1.35

        tx = center[0] + math.cos(mid_angle) * text_radius
        ty = center[1] + math.sin(mid_angle) * text_radius

        bbox = draw.textbbox((0, 0), pct_text, font=FONT_BODY)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        draw.text(
            (
                tx - text_w / 2,
                ty - text_h / 2,
            ),
            pct_text,
            font=FONT_BODY,
            fill=COLORS["text"],
        )

        start = end

    # Labels
    if legend_x is None:
        legend_x = center[0] + radius + 45

    if legend_y is None:
        legend_y = center[1] - 100

    legend_data = sorted(
        zip(labels, values, colors),
        key=lambda x: x[1],
        reverse=True,
    )

    for i, (label, value, color) in enumerate(legend_data):
        y = legend_y + i * 42
        draw.ellipse([legend_x, y + 6, legend_x + 20, y + 26], fill=color, outline=COLORS["gold_dim"])
        draw.text((legend_x + 34, y), label, font=FONT_BODY, fill=COLORS["text"])
        draw.text((legend_x + 160, y), str(value), font=FONT_BODY, fill=COLORS["text"])


def draw_radar(draw, center, radius, series, colors, labels):
    axes = 5
    angles = [(-90 + i * 360 / axes) * math.pi / 180 for i in range(axes)]

    # Grid
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = [
            (
                center[0] + math.cos(a) * radius * level,
                center[1] + math.sin(a) * radius * level,
            )
            for a in angles
        ]
        draw.line(pts + [pts[0]], fill=COLORS["gold_dim"], width=2)

    for a in angles:
        draw.line(
            [
                center,
                (
                    center[0] + math.cos(a) * radius,
                    center[1] + math.sin(a) * radius,
                ),
            ],
            fill=COLORS["gold_dim"],
            width=1,
        )

    # Series
    for vals, color in zip(series, colors):
        pts = [
            (
                center[0] + math.cos(a) * radius * (v / 100),
                center[1] + math.sin(a) * radius * (v / 100),
            )
            for a, v in zip(angles, vals)
        ]
        draw.line(pts + [pts[0]], fill=color, width=3)

    # Small labels
    for label, a in zip(labels, angles):
        lx = center[0] + math.cos(a) * (radius + 34)
        ly = center[1] + math.sin(a) * (radius + 34)

        bbox = draw.textbbox((0, 0), label, font=FONT_SMALL)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        draw.text(
            (
                lx - text_w / 2,
                ly - text_h / 2,
            ),
            label,
            font=FONT_SMALL,
            fill=COLORS["muted"],
        )


def draw_bar_chart(draw, box, labels, players, completions):
    x1, y1, x2, y2 = box
    max_players = max(players) if players else 1
    max_completions = max(completions) if completions else 1

    left_label_size = draw.textbbox((0, 0), f"{int(round(max_players))}", font=FONT_SMALL)
    left_padding = left_label_size[2]-left_label_size[0]
    right_label_size = draw.textbbox((0, 0), f"{int(round(max_completions))}", font=FONT_SMALL)
    right_padding = right_label_size[2] - right_label_size[0]

    chart_x1 = x1 + left_padding + 10
    chart_y1 = y1 + 100
    chart_x2 = x2 - right_padding - 10
    chart_y2 = y2 - 70

    draw.line([(chart_x1, chart_y1), (chart_x1, chart_y2)], fill=COLORS["gold_dim"], width=2)
    draw.line([(chart_x2, chart_y1), (chart_x2, chart_y2)], fill=COLORS["gold_dim"], width=2)
    draw.line([(chart_x1 - 8, chart_y2), (chart_x2+8, chart_y2)], fill=COLORS["gold_dim"], width=2)

    tick_count = 4
    for i in range(tick_count + 1):
        players_value = max_players * i / tick_count
        completions_value = max_completions * i / tick_count
        tick_y = chart_y2 - (chart_y2 - chart_y1) * i / tick_count

        draw.line(
            [(chart_x1 - 5, tick_y), (chart_x2 + 5, tick_y)],
            fill=COLORS["gold_dim"],
            width=2,
        )

        tick_label = f"{int(round(players_value))}"
        bbox = draw.textbbox((0, 0), tick_label, font=FONT_SMALL)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        draw.text(
            (chart_x1 - 12 - text_w, tick_y - text_h // 2),
            tick_label,
            font=FONT_SMALL,
            fill=COLORS["muted"],
        )

        tick_label = f"{int(round(completions_value))}"
        bbox = draw.textbbox((0, 0), tick_label, font=FONT_SMALL)
        text_h = bbox[3] - bbox[1]

        draw.text(
            (chart_x2 + 12, tick_y - text_h // 2),
            tick_label,
            font=FONT_SMALL,
            fill=COLORS["muted"],
        )

    group_w = (chart_x2 - chart_x1) / len(labels)
    bar_w = group_w * 0.28

    for i, label in enumerate(labels):
        gx = chart_x1 + i * group_w + group_w * 0.22

        p_h = (players[i] / max_players) * (chart_y2 - chart_y1)
        c_h = (completions[i] / max_completions) * (chart_y2 - chart_y1)

        player_color = ARCHETYPE_PCOLORS.get(label)
        completion_COLOR = ARCHETYPE_CCOLORS.get(label)

        draw.rectangle(
            [gx, chart_y2 - p_h, gx + bar_w, chart_y2],
            fill=player_color,
        )
        draw.rectangle(
            [gx + bar_w + 8, chart_y2 - c_h, gx + bar_w * 2 + 8, chart_y2],
            fill=completion_COLOR,
        )

        label_x = gx + bar_w + 3

        bbox = draw.textbbox((0, 0), label, font=FONT_SMALL)
        text_w = bbox[2] - bbox[0]

        draw.text(
            (label_x - text_w / 2, chart_y2 + 10),
            label,
            font=FONT_SMALL,
            fill=COLORS["text"],
        )

        bbox = draw.textbbox((0, 0), f"|", font=FONT_SMALLER)
        text_w = bbox[2] - bbox[0]

        draw.text(
            (label_x - text_w / 2, chart_y2 + 32),
            f"|",
            font=FONT_SMALL,
            fill=COLORS["text"],
        )

        bbox = draw.textbbox((0, 0), f"{players[i]}", font=FONT_SMALLER)
        text_w = bbox[2] - bbox[0]

        draw.text(
            (label_x - text_w - 7, chart_y2 + 32),
            f"{players[i]}",
            font=FONT_SMALL,
            fill=COLORS["text"],
        )

        draw.text(
            (label_x + 3, chart_y2 + 32),
            f"{completions[i]}",
            font=FONT_SMALL,
            fill=COLORS["text"],
        )

    title = "Archetype Tallies For Today"

    bbox = draw.textbbox((0, 0), title, font=FONT_SECTION)
    text_w = bbox[2] - bbox[0]

    draw.text(
        (
            (x1 + x2) / 2 - text_w / 2,
            y1 + 25,
        ),
        title,
        font=FONT_SECTION,
        fill=COLORS["title_text"],
    )

    caption = "Players on the left, completions on the right"
    caption_bbox = draw.textbbox((0, 0), caption, font=FONT_SMALL)
    caption_w = caption_bbox[2] - caption_bbox[0]

    draw.text(
        (
            (x1 + x2) / 2 - caption_w / 2,
            y1 + 62,
        ),
        caption,
        font=FONT_SMALL,
        fill=COLORS["muted"],
    )


def paste_icon(img):
    if not ICON_PATH.exists():
        return

    icon = Image.open(ICON_PATH).convert("RGBA")
    icon.thumbnail((650, 375))

    x = W//2-icon.size[0] - 10
    y = 40

    img.alpha_composite(icon, (x, y))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (W, H), COLORS["bg"])
    add_noise_background(img)

    draw = ImageDraw.Draw(img)

    draw_outer_border(draw)
    paste_icon(img)

    draw_centered_text(draw, W // 2, W - 30, "Daily Raid Analysis", 150, FONT_TITLE, COLORS["text"])
    draw_centered_text(draw, W // 2, W - 30, "Date: 2026-05-14", 250, FONT_SUBTITLE, COLORS["title_text"])
    draw_centered_text(draw, W // 2, W - 30, "Total Completions: 4639", 300, FONT_SUBTITLE, COLORS["title_text"])

    draw_divider(draw, 405)

    # Top pies
    pie_y = 650
    pie_radius = 130

    left_region = (80, 430, W // 2 - 30, 850)
    right_region = (W // 2 + 30, 430, W - 80, 850)

    def draw_pie_region(_draw, region, title, values, labels, colors):
        x1, y1, x2, y2 = region
        region_w = x2 - x1

        pie_center = (
            x1 + region_w * 0.3,
            pie_y,
        )

        title_bbox = _draw.textbbox((0, 0), title, font=FONT_SECTION)
        title_w = title_bbox[2] - title_bbox[0]

        _draw.text(
            (
                x1 + region_w / 2 - title_w / 2,
                y1,
            ),
            title,
            font=FONT_SECTION,
            fill=COLORS["title_text"],
        )

        draw_pie(
            _draw,
            center=pie_center,
            radius=pie_radius,
            values=values,
            labels=labels,
            colors=colors,
            legend_x=x1 + region_w * 0.7,
            legend_y=pie_y - 105,
        )

    draw_pie_region(
        draw,
        left_region,
        "Players",
        values=[30 + int(random.random() * 600) for _ in range(5)],
        labels=CLASS_LIST,
        colors=[COLORS[i] for i in CLASS_LIST],
    )

    draw_pie_region(
        draw,
        right_region,
        "Completions",
        values=[300 + int(random.random() * 1000) for _ in range(5)],
        labels=CLASS_LIST,
        colors=[COLORS[i] for i in CLASS_LIST],
    )

    draw_divider(draw, 860)

    # Ultimate usage panel
    panel_width = 240
    left_margin = right_margin = 50

    panel = (
        W - right_margin - panel_width,
        880,
        W - right_margin,
        1320,
    )
    panel_x1, panel_y1, panel_x2, panel_y2 = panel

    draw_panel(draw, panel, "Ultimate Usage")
    ult_lines = list(zip(ARCHETYPE_LIST, [f"{round(random.random() *50 + random.random() *50,2):.1f}%" for _ in range(15)]))


    label_x = panel_x1 + 22
    value_x = panel_x2 - 22

    top_y = panel_y1 + 78
    bottom_y = panel_y2 - 36

    available_height = bottom_y - top_y
    line_spacing = available_height / len(ult_lines)

    for i, (label, val) in enumerate(ult_lines):
        y = top_y + i * line_spacing

        # Left aligned label
        draw.text(
            (label_x, y),
            label,
            font=FONT_SMALL,
            fill=COLORS["text"],
        )

        # Right aligned value
        bbox = draw.textbbox((0, 0), val, font=FONT_SMALL)
        text_w = bbox[2] - bbox[0]

        draw.text(
            (value_x - text_w, y),
            val,
            font=FONT_SMALL,
            fill=COLORS["text"],
        )

    # Radars
    radar_names = RADAR_FIXED

    radar_radius = 90
    radar_label_padding = 45
    radar_visual_radius = radar_radius + radar_label_padding
    radar_top_y = 1120
    radar_stagger = 65

    radar_area_x1 = left_margin + radar_visual_radius

    panel_gap = 25
    radar_area_x2 = panel_x1 - panel_gap - radar_visual_radius

    radar_spacing = (radar_area_x2 - radar_area_x1) / (len(radar_names) - 1)

    radar_positions = []

    for i, name in enumerate(radar_names):
        cx = radar_area_x1 + i * radar_spacing
        cy = radar_top_y + (radar_stagger if i % 2 else 0)
        radar_positions.append((cx, cy, name))

    radar_title = "Skill Point Averages"

    bbox = draw.textbbox((0, 0), radar_title, font=FONT_SECTION)
    text_w = bbox[2] - bbox[0]

    draw.text(
        (
            (radar_area_x1 + radar_area_x2) / 2 - text_w / 2,
            890,
        ),
        radar_title,
        font=FONT_SECTION,
        fill=COLORS["title_text"],
    )

    for cx, cy, radar_class in radar_positions:
        label_bbox = draw.textbbox((0, 0), radar_class, font=FONT_BODY)
        label_w = label_bbox[2] - label_bbox[0]

        draw.text(
            (cx - label_w / 2, cy - 170),
            radar_class,
            font=FONT_BODY,
            fill=COLORS["title_text"],
        )

        archetypes = RADAR_ARCHCLASS[radar_class]
        radar_values = [
            [random.randint(20, 70), random.randint(20, 70), random.randint(20, 70), random.randint(20, 70), random.randint(20, 70)]
            for _ in archetypes
        ]
        radar_colors = [ARCHETYPE_PCOLORS[archetype] for archetype in archetypes]

        draw_radar(
            draw,
            center=(cx, cy),
            radius=radar_radius,
            series=radar_values,
            colors=radar_colors,
            labels=["Str", "Dex", "Int", "Def", "Agi"],
        )

    draw_divider(draw, 1340)

    # Bar chart
    draw_bar_chart(
        draw,
        box=(50, 1350, 1550, 1750),
        labels=ARCHETYPE_LIST,
        players=[10 + int(random.random() * 200) for _ in range(15)],
        completions=[500 + int(random.random() * 800) for _ in range(15)],
    )

    img.save(OUTPUT_PATH)
    print(f"Saved dashboard test image to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
