import asyncio
from itertools import cycle
from typing import Any, Optional

import aiohttp

from src.api.rate_limiter import RateLimiter
from src.config.settings import (
    WYNN_API_KEYS,
    REQUEST_TIMEOUT_SECONDS,
)
from src.utils.logging_utils import setup_logger


logger = setup_logger(__name__)


RAID_NAME_TO_FIELD = {
    "Nest of the Grootslangs": "nog",
    "Orphion's Nexus of Light": "nol",
    "The Canyon Colossus": "tcc",
    "The Nameless Anomaly": "tna",
    "The Wartorn Palace": "wtp",
}


class WynnAPI:
    BASE_URL = "https://api.wynncraft.com/v3"

    def __init__(self):
        self.api_keys = WYNN_API_KEYS

        if not self.api_keys:
            logger.warning("No Wynn API keys configured; using unauthenticated requests")

        self.key_cycle = cycle(self.api_keys) if self.api_keys else None

        self.limiters = {
            key: RateLimiter(max_calls=100, period_seconds=60)
            for key in self.api_keys
        }

        self.anon_limiter = RateLimiter(max_calls=30, period_seconds=60)

        self.timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)

    def _get_next_key(self) -> Optional[str]:
        if not self.key_cycle:
            return None

        return next(self.key_cycle)

    async def _request_json(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        retries: int = 3,
    ) -> Optional[dict[str, Any]]:
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(1, retries + 1):
            api_key = self._get_next_key()

            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                await self.limiters[api_key].acquire()
            else:
                await self.anon_limiter.acquire()

            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        logger.info(f"404 not found: {endpoint}")
                        return None

                    if response.status == 429:
                        wait_time = 5 * attempt
                        logger.warning(f"429 rate limited for {endpoint}; sleeping {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status in {500, 502, 503, 504}:
                        wait_time = 10 * attempt
                        logger.warning(
                            f"{response.status} server error for {endpoint}; sleeping {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status >= 400:
                        text = await response.text()
                        logger.warning(
                            f"HTTP {response.status} for {endpoint}: {text[:300]}"
                        )
                        return None

                    return await response.json()

            except asyncio.TimeoutError:
                wait_time = 5 * attempt
                logger.warning(f"Timeout for {endpoint}; sleeping {wait_time}s")
                await asyncio.sleep(wait_time)

            except aiohttp.ClientError:
                wait_time = 5 * attempt
                logger.exception(f"Client error for {endpoint}; sleeping {wait_time}s")
                await asyncio.sleep(wait_time)

        logger.error(f"Failed after retries: {endpoint}")
        return None

    async def fetch_online_players(
        self,
        session: aiohttp.ClientSession,
    ) -> Optional[dict[str, Any]]:
        return await self._request_json(session, "/player?identifier=uuid")

    async def fetch_player(
        self,
        session: aiohttp.ClientSession,
        player_id: str,
    ) -> Optional[dict[str, Any]]:
        return await self._request_json(session, f"/player/{player_id}?fullResult=")

    async def fetch_atree(
        self,
        session: aiohttp.ClientSession,
        player_id: str,
        character_id: str,
    ) -> Optional[dict[str, Any]]:
        return await self._request_json(
            session,
            f"/player/{player_id}/characters/{character_id}/abilities",
        )

    def parse_online_players(self, payload: dict[str, Any]) -> tuple[int, list[str]]:
        """
        Expected online endpoint shape:
            {
                "total": 1234,
                "players": {
                    "uuid": "server",
                    ...
                }
            }
        """
        total = int(payload.get("total", 0) or 0)
        players = payload.get("players", {}) or {}

        if not isinstance(players, dict):
            logger.warning("Online players payload had invalid players field")
            return total, []

        return total, list(players.keys())

    def parse_player_characters(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extracts level 119+ character-level raid totals and skill points.

        Rules:
        - Missing raid names are treated as 0.
        - If skillPoints is removed/hidden, all skill point fields are None.
        - If skillPoints exists, missing individual skills are treated as 0.
        """
        player_id = payload.get("uuid")
        player_name = payload.get("username")

        characters = payload.get("characters")
        restrictions = payload.get("restrictions", {})
        character_build_access = restrictions.get("characterBuildAccess")

        if not player_id or not isinstance(characters, dict):
            is_main_access_restricted = restrictions.get("mainAccess") is True

            if is_main_access_restricted or not isinstance(characters, dict):
                logger.info(
                    f"Skipping player due to inaccessible character data: "
                    f"username={player_name}, uuid={player_id}"
                )
            else:
                logger.info(
                    f"Skipping player with unexpected character parsing failure: "
                    f"username={player_name}, uuid={player_id}, "
                    f"restrictions={restrictions}, "
                    f"error={payload.get('error')}, "
                    f"detail={payload.get('detail')}, "
                    f"code={payload.get('code')}, "
                    f"keys={list(payload.keys())}"
                )

            return []

        parsed = []

        for character_id, character in characters.items():
            if not isinstance(character, dict):
                continue

            character_level = int(character.get("level", 0) or 0)

            if character_level < 119:
                continue

            raids = character.get("raids")
            if not isinstance(raids, dict):
                continue

            raid_list = raids.get("list", {})
            if not isinstance(raid_list, dict):
                raid_list = {}

            removed_stats = character.get("removedStat", [])
            if not isinstance(removed_stats, list):
                removed_stats = []

            skill_points_removed = "skillPoints" in removed_stats
            skill_points = character.get("skillPoints")

            if skill_points_removed:
                str_points = None
                dex_points = None
                int_points = None
                def_points = None
                agi_points = None
            elif isinstance(skill_points, dict):
                str_points = skill_points.get("strength", 0)
                dex_points = skill_points.get("dexterity", 0)
                int_points = skill_points.get("intelligence", 0)
                def_points = skill_points.get("defence", 0)
                agi_points = skill_points.get("agility", 0)
            else:
                str_points = None
                dex_points = None
                int_points = None
                def_points = None
                agi_points = None

            parsed.append({
                "player_id": player_id,
                "player_name": player_name,
                "character_id": character_id,
                "character_type": character.get("type"),
                "character_build_access": character_build_access,
                "removed_stats": removed_stats,

                "nog_total": int(raid_list.get("Nest of the Grootslangs", 0) or 0),
                "nol_total": int(raid_list.get("Orphion's Nexus of Light", 0) or 0),
                "tcc_total": int(raid_list.get("The Canyon Colossus", 0) or 0),
                "tna_total": int(raid_list.get("The Nameless Anomaly", 0) or 0),
                "wtp_total": int(raid_list.get("The Wartorn Palace", 0) or 0),

                "str": str_points,
                "dex": dex_points,
                "int": int_points,
                "def": def_points,
                "agi": agi_points,
            })

        return parsed

    async def create_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(timeout=self.timeout)