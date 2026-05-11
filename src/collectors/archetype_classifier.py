from typing import Any, Optional

from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


CLASS_ARCHETYPES = {
    "ARCHER": [
        "Boltslinger",
        "Sharpshooter",
        "Trapper",
    ],
    "ASSASSIN": [
        "Shadestepper",
        "Trickster",
        "Acrobat",
    ],
    "MAGE": [
        "Arcanist",
        "Riftwalker",
        "Light Bender",
    ],
    "SHAMAN": [
        "Summoner",
        "Ritualist",
        "Acolyte",
    ],
    "WARRIOR": [
        "Fallen",
        "Battle Monk",
        "Paladin",
    ],
}


# Fill these marker lists in later.
# Use ability IDs from node["meta"]["id"].
ARCHETYPE_MARKERS = {
    "Boltslinger": ["helicopter"], # Arrow Hurricane
    "Sharpshooter": ["concentration"],
    "Trapper": ["manaTrap"],

    "Shadestepper": ["nightcloakKnives"],
    "Trickster": ["echo"],
    "Acrobat": ["jasminBloom"],

    "Arcanist": ["chaosExplosion"],
    "Riftwalker": ["riftbound"],
    "Light Bender": ["massImmune"], # Sunflare

    "Summoner": ["hummingbirds"],
    "Ritualist": ["maskOfTheAwakened"],
    "Acolyte": ["bloodPool"],

    "Fallen": ["betterEnragedBlow"],
    "Battle Monk": ["bigHands"], # Pressure
    "Paladin": ["heavenlyTrumpet"],
}


def classify_archetype(
    atree_payload: Any,
    character_type: str,
) -> Optional[str]:
    """
    Returns one of the 15 archetype names, or None if unknown/unavailable.

    The abilities endpoint is expected to return a list of nodes.
    We classify by checking selected ability IDs against archetype marker IDs.
    """
    if not atree_payload:
        return None

    character_type = character_type.upper()

    possible_archetypes = CLASS_ARCHETYPES.get(character_type)

    if not possible_archetypes:
        logger.warning(f"Unknown character type for archetype classification: {character_type}")
        return None

    selected_abilities = extract_selected_abilities(atree_payload)

    if not selected_abilities:
        return None

    scores = score_archetypes(
        selected_abilities=selected_abilities,
        possible_archetypes=possible_archetypes,
    )

    if not scores:
        return None

    best_archetype, best_score = max(
        scores.items(),
        key=lambda item: item[1],
    )

    if best_score <= 0:
        return None

    return best_archetype


def extract_selected_abilities(atree_payload: Any) -> set[str]:
    """
    Wynn abilities endpoint returns a list of nodes.

    We only care about real ability nodes:
        node["type"] == "ability"
        node["meta"]["id"]
    """
    selected = set()

    if not isinstance(atree_payload, list):
        logger.warning(f"Unexpected atree payload type: {type(atree_payload)}")
        return selected

    for node in atree_payload:
        if not isinstance(node, dict):
            continue

        if node.get("type") != "ability":
            continue

        meta = node.get("meta", {})
        if not isinstance(meta, dict):
            continue

        ability_id = meta.get("id")

        if ability_id:
            selected.add(str(ability_id))

    return selected


def score_archetypes(
    selected_abilities: set[str],
    possible_archetypes: list[str],
) -> dict[str, int]:
    scores = {}

    for archetype in possible_archetypes:
        markers = ARCHETYPE_MARKERS.get(archetype, [])

        score = sum(
            1
            for marker in markers
            if marker in selected_abilities
        )

        scores[archetype] = score

    return scores