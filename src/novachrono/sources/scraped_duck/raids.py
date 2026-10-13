from typing import Any, Final

from novachrono.models.pokemon_go import (
    RaidBoss,
    RaidRoster,
    RaidTier,
)
from novachrono.sources.scraped_duck._common import (
    DEFAULT_TIMEOUT_SECONDS,
    ScrapedDuckError,
    _fetch_entries,
    _read_optional_image_url,
    _read_string,
    _validate_timeout,
)

SCRAPED_DUCK_RAIDS_URL: Final = (
    "https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/raids.min.json"
)
SHADOW_RAID_PREFIX: Final = "shadow "


def fetch_raid_roster(
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> RaidRoster:
    """Retrieve and normalize current 5-star, Shadow 5-star, and Mega raids."""

    _validate_timeout(timeout_seconds)

    return _parse_raid_roster(
        _fetch_entries(SCRAPED_DUCK_RAIDS_URL, timeout_seconds=timeout_seconds)
    )


def _parse_raid_roster(entries: list[Any]) -> RaidRoster:
    five_star: list[RaidBoss] = []
    mega: list[RaidBoss] = []
    shadow_five_star: list[RaidBoss] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        tier = _parse_raid_tier(entry.get("tier"))

        if tier is None:
            continue

        is_shadow = _is_shadow_raid(entry)

        if is_shadow and tier is not RaidTier.FIVE_STAR:
            continue

        raid_boss = _parse_raid_boss(entry, strip_shadow_prefix=is_shadow)

        if is_shadow:
            shadow_five_star.append(raid_boss)
        elif tier is RaidTier.FIVE_STAR:
            five_star.append(raid_boss)
        else:
            mega.append(raid_boss)

    return RaidRoster(
        five_star=tuple(five_star),
        mega=tuple(mega),
        shadow_five_star=tuple(shadow_five_star),
    )


def _parse_raid_tier(value: Any) -> RaidTier | None:
    if value in {"5-Star Raids", "Tier 5"}:
        return RaidTier.FIVE_STAR

    if value in {"Mega Raids", "Mega"}:
        return RaidTier.MEGA

    return None


def _is_shadow_raid(data: dict[str, Any]) -> bool:
    name = data.get("name")

    if not isinstance(name, str):
        return False

    return name.strip().casefold().startswith(SHADOW_RAID_PREFIX)


def _parse_raid_boss(
    data: dict[str, Any],
    *,
    strip_shadow_prefix: bool = False,
) -> RaidBoss:
    name = _read_string(data, "name")

    if strip_shadow_prefix:
        name = _strip_shadow_prefix(name)

    return RaidBoss(
        name=name,
        can_be_shiny=_read_boolean(data, "canBeShiny"),
        artwork_url=_read_optional_image_url(data, "image"),
    )


def _strip_shadow_prefix(name: str) -> str:
    normalized_name = name.strip()

    if not normalized_name.casefold().startswith(SHADOW_RAID_PREFIX):
        return normalized_name

    stripped_name = normalized_name[len(SHADOW_RAID_PREFIX) :].strip()

    if not stripped_name:
        raise ScrapedDuckError("ScrapedDuck shadow raid contains an invalid 'name'")

    return stripped_name


def _read_boolean(
    data: dict[str, Any],
    name: str,
) -> bool:
    value = data.get(name)

    if not isinstance(value, bool):
        raise ScrapedDuckError(f"ScrapedDuck data contains invalid '{name}'")

    return value
