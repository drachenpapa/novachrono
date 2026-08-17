import json
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from novachrono.pokemon_go import (
    CombatPowerRange,
    PokemonType,
    RaidBoss,
    RaidRoster,
    RaidTier,
)

SCRAPED_DUCK_RAIDS_URL: Final = (
    "https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/raids.min.json"
)
DEFAULT_TIMEOUT_SECONDS: Final = 8.0

SHADOW_RAID_PREFIX: Final = "shadow "


class ScrapedDuckError(RuntimeError):
    """Raised when ScrapedDuck Pokémon GO raid data cannot be retrieved."""


def fetch_raid_roster(
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> RaidRoster:
    """Retrieve and normalize the current regular 5-star and Mega raid roster."""

    if timeout_seconds <= 0:
        raise ValueError("ScrapedDuck timeout must be greater than zero")

    request = Request(
        url=SCRAPED_DUCK_RAIDS_URL,
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urlopen(  # nosec B310 - fixed HTTPS endpoint
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise ScrapedDuckError(f"ScrapedDuck returned HTTP {error.code}: {error.reason}") from error
    except URLError as error:
        raise ScrapedDuckError(f"Could not reach ScrapedDuck: {error.reason}") from error
    except TimeoutError as error:
        raise ScrapedDuckError("Connection to ScrapedDuck timed out") from error

    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise ScrapedDuckError("ScrapedDuck returned invalid JSON") from error

    if not isinstance(response_data, list):
        raise ScrapedDuckError("ScrapedDuck returned an unexpected response")

    return _parse_raid_roster(response_data)


def _parse_raid_roster(entries: list[Any]) -> RaidRoster:
    five_star: list[RaidBoss] = []
    mega: list[RaidBoss] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        tier = _parse_raid_tier(entry.get("tier"))

        if tier is None:
            continue

        if _is_shadow_raid(entry):
            continue

        raid_boss = _parse_raid_boss(
            entry,
            tier=tier,
        )

        if tier is RaidTier.FIVE_STAR:
            five_star.append(raid_boss)
        else:
            mega.append(raid_boss)

    return RaidRoster(
        five_star=tuple(five_star),
        mega=tuple(mega),
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
    tier: RaidTier,
) -> RaidBoss:
    name = _read_string(data, "name")
    can_be_shiny = _read_boolean(data, "canBeShiny")
    types = _read_types(data)
    artwork_url = _read_optional_image_url(data, "image")

    combat_power = _read_mapping(data, "combatPower")
    normal_combat_power = _read_combat_power_range(
        combat_power,
        "normal",
    )
    boosted_combat_power = _read_combat_power_range(
        combat_power,
        "boosted",
    )

    return RaidBoss(
        name=name,
        tier=tier,
        can_be_shiny=can_be_shiny,
        types=types,
        normal_combat_power=normal_combat_power,
        boosted_combat_power=boosted_combat_power,
        artwork_url=artwork_url,
    )


def _read_types(
    data: dict[str, Any],
) -> tuple[PokemonType, ...]:
    raw_types = data.get("types")

    if not isinstance(raw_types, list) or not raw_types:
        raise ScrapedDuckError("ScrapedDuck raid contains invalid 'types'")

    parsed_types: list[PokemonType] = []

    for raw_type in raw_types:
        if not isinstance(raw_type, dict):
            raise ScrapedDuckError("ScrapedDuck raid contains invalid 'types'")

        type_name = _read_string(
            raw_type,
            "name",
        ).lower()

        try:
            pokemon_type = PokemonType(type_name)
        except ValueError as error:
            raise ScrapedDuckError(
                f"ScrapedDuck raid contains unsupported Pokemon type: {type_name}"
            ) from error

        parsed_types.append(pokemon_type)

    return tuple(parsed_types)


def _read_combat_power_range(
    data: dict[str, Any],
    name: str,
) -> CombatPowerRange:
    values = _read_mapping(data, name)

    minimum = _read_integer(values, "min")
    maximum = _read_integer(values, "max")

    if minimum > maximum:
        raise ScrapedDuckError(f"ScrapedDuck raid contains invalid '{name}' combat power range")

    return CombatPowerRange(
        minimum=minimum,
        maximum=maximum,
    )


def _read_mapping(
    data: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    value = data.get(name)

    if not isinstance(value, dict):
        raise ScrapedDuckError(f"ScrapedDuck raid contains invalid '{name}'")

    return value


def _read_string(
    data: dict[str, Any],
    name: str,
) -> str:
    value = data.get(name)

    if not isinstance(value, str) or not value.strip():
        raise ScrapedDuckError(f"ScrapedDuck raid contains invalid '{name}'")

    return value.strip()


def _read_boolean(
    data: dict[str, Any],
    name: str,
) -> bool:
    value = data.get(name)

    if not isinstance(value, bool):
        raise ScrapedDuckError(f"ScrapedDuck raid contains invalid '{name}'")

    return value


def _read_integer(
    data: dict[str, Any],
    name: str,
) -> int:
    value = data.get(name)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ScrapedDuckError(f"ScrapedDuck raid contains invalid '{name}'")

    return value


def _read_optional_image_url(
    data: dict[str, Any],
    name: str,
) -> str | None:
    value = data.get(name)

    if not isinstance(value, str):
        return None

    normalized_value = value.strip()
    parsed_url = urlparse(normalized_value)

    if parsed_url.scheme.casefold() != "https" or parsed_url.hostname is None:
        return None

    return normalized_value
