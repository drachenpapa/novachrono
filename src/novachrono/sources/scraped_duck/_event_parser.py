import re
from datetime import datetime, tzinfo
from typing import Any, Final

from novachrono.models.pokemon_go import (
    PokemonGoEvent,
    PokemonGoEventType,
    PokemonGoFeaturedPokemon,
)
from novachrono.sources.scraped_duck._common import (
    ScrapedDuckError,
    _read_optional_image_url,
    _read_string,
)

COMMUNITY_DAY_EVENT_TYPE: Final = "community-day"
SPOTLIGHT_HOUR_EVENT_TYPE: Final = "pokemon-spotlight-hour"
MAX_MONDAY_EVENT_TYPE: Final = "max-mondays"

_COMMUNITY_DAY_PLACEHOLDER_NAMES: Final = frozenset(
    {
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    }
)


def _parse_event_type(data: dict[str, Any]) -> PokemonGoEventType | None:
    value = data.get("eventType")

    if value == COMMUNITY_DAY_EVENT_TYPE:
        if _is_community_day_classic(data):
            return PokemonGoEventType.COMMUNITY_DAY_CLASSIC

        return PokemonGoEventType.COMMUNITY_DAY

    if value == SPOTLIGHT_HOUR_EVENT_TYPE:
        return PokemonGoEventType.SPOTLIGHT_HOUR

    if value == MAX_MONDAY_EVENT_TYPE:
        return PokemonGoEventType.MAX_MONDAY

    return None


def _is_community_day_classic(data: dict[str, Any]) -> bool:
    for field_name in ("name", "heading"):
        value = data.get(field_name)

        if isinstance(value, str) and "classic" in value.casefold():
            return True

    return False


def _parse_event(
    data: dict[str, Any],
    *,
    event_type: PokemonGoEventType,
    local_timezone: tzinfo,
) -> PokemonGoEvent | None:
    name = _read_string(data, "name")
    start = _parse_event_datetime(data, "start", local_timezone=local_timezone)
    end = _parse_event_datetime(data, "end", local_timezone=local_timezone)

    if start is None or end is None:
        return None

    if end <= start:
        raise ScrapedDuckError("ScrapedDuck event contains an invalid time range")

    if event_type in {PokemonGoEventType.COMMUNITY_DAY, PokemonGoEventType.COMMUNITY_DAY_CLASSIC}:
        featured_pokemon, bonus = _parse_community_day_details(data, event_name=name)

    elif event_type is PokemonGoEventType.SPOTLIGHT_HOUR:
        featured_pokemon, bonus = _parse_spotlight_hour_details(data, event_name=name)

    else:
        featured_pokemon = _parse_max_monday_details(name)
        bonus = None

    return PokemonGoEvent(
        event_type=event_type,
        name=name,
        start=start,
        end=end,
        featured_pokemon=featured_pokemon,
        bonus=bonus,
    )


def _parse_community_day_details(
    data: dict[str, Any],
    *,
    event_name: str,
) -> tuple[tuple[PokemonGoFeaturedPokemon, ...], str | None]:
    community_day = _read_nested_object(data, "extraData", "communityday")

    if community_day is None:
        return (_featured_pokemon_from_names(_parse_community_day_pokemon_names(event_name)), None)

    featured_pokemon: list[PokemonGoFeaturedPokemon] = []
    spawns = community_day.get("spawns")
    shinies = community_day.get("shinies")

    if isinstance(spawns, list):
        for spawn in spawns:
            if not isinstance(spawn, dict):
                continue

            name = _read_optional_string(spawn, "name")

            if name is None:
                continue

            featured_pokemon.append(
                PokemonGoFeaturedPokemon(
                    name=name,
                    can_be_shiny=_read_shiny_availability(shinies, pokemon_name=name),
                    artwork_url=_read_optional_image_url(spawn, "image"),
                )
            )

    if not featured_pokemon:
        featured_pokemon.extend(
            _featured_pokemon_from_names(_parse_community_day_pokemon_names(event_name))
        )

    return (
        _deduplicate_featured_pokemon(featured_pokemon),
        _read_community_day_bonus(community_day.get("bonuses")),
    )


def _parse_spotlight_hour_details(
    data: dict[str, Any],
    *,
    event_name: str,
) -> tuple[tuple[PokemonGoFeaturedPokemon, ...], str | None]:
    spotlight = _read_nested_object(data, "extraData", "spotlight")

    if spotlight is None:
        return (_featured_pokemon_from_names(_parse_spotlight_hour_pokemon_names(event_name)), None)

    featured_pokemon: list[PokemonGoFeaturedPokemon] = []
    entries = spotlight.get("list")

    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            featured = _parse_spotlight_featured_pokemon(entry)

            if featured is not None:
                featured_pokemon.append(featured)

    if not featured_pokemon:
        featured = _parse_spotlight_featured_pokemon(spotlight)

        if featured is not None:
            featured_pokemon.append(featured)

    if not featured_pokemon:
        featured_pokemon.extend(
            _featured_pokemon_from_names(_parse_spotlight_hour_pokemon_names(event_name))
        )

    return (
        _deduplicate_featured_pokemon(featured_pokemon),
        _read_optional_string(spotlight, "bonus"),
    )


def _parse_spotlight_featured_pokemon(data: dict[str, Any]) -> PokemonGoFeaturedPokemon | None:
    name = _read_optional_string(data, "name")

    if name is None:
        return None

    return PokemonGoFeaturedPokemon(
        name=name,
        can_be_shiny=_read_optional_boolean(data, "canBeShiny"),
        artwork_url=_read_optional_image_url(data, "image"),
    )


def _parse_max_monday_details(event_name: str) -> tuple[PokemonGoFeaturedPokemon, ...]:
    normalized_name = _strip_suffix(event_name, " during Max Monday")

    if normalized_name == event_name.strip():
        return ()

    names = tuple(
        _strip_dynamax_prefix(name)
        for name in _split_featured_names(_strip_dynamax_prefix(normalized_name))
    )

    return _featured_pokemon_from_names(names)


def _parse_community_day_pokemon_names(event_name: str) -> tuple[str, ...]:
    normalized_name = event_name.strip()

    for suffix in (" Community Day Classic", " Community Day"):
        without_suffix = _strip_suffix(normalized_name, suffix)

        if without_suffix == normalized_name:
            continue

        if without_suffix.casefold() in _COMMUNITY_DAY_PLACEHOLDER_NAMES:
            return ()

        return _split_featured_names(without_suffix)

    return ()


def _parse_spotlight_hour_pokemon_names(event_name: str) -> tuple[str, ...]:
    without_suffix = _strip_suffix(event_name, " Spotlight Hour")

    if without_suffix == event_name.strip():
        return ()

    return _split_featured_names(without_suffix)


def _split_featured_names(value: str) -> tuple[str, ...]:
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+|\s*&\s*", value.strip(), flags=re.IGNORECASE)

    return tuple(part.strip() for part in parts if part.strip())


def _strip_dynamax_prefix(name: str) -> str:
    normalized_name = name.strip()

    for prefix in ("Dynamax ", "Gigantamax "):
        if normalized_name.casefold().startswith(prefix.casefold()):
            return normalized_name[len(prefix) :].strip()

    return normalized_name


def _featured_pokemon_from_names(names: tuple[str, ...]) -> tuple[PokemonGoFeaturedPokemon, ...]:
    return tuple(PokemonGoFeaturedPokemon(name=name) for name in names if name)


def _deduplicate_featured_pokemon(
    pokemon: list[PokemonGoFeaturedPokemon],
) -> tuple[PokemonGoFeaturedPokemon, ...]:
    unique: list[PokemonGoFeaturedPokemon] = []
    seen_names: set[str] = set()

    for featured in pokemon:
        normalized_name = featured.name.casefold()

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)
        unique.append(featured)

    return tuple(unique)


def _strip_suffix(
    value: str,
    suffix: str,
) -> str:
    normalized_value = value.strip()

    if not normalized_value.casefold().endswith(suffix.casefold()):
        return normalized_value

    return normalized_value[: -len(suffix)].strip()


def _parse_event_datetime(
    data: dict[str, Any],
    name: str,
    *,
    local_timezone: tzinfo,
) -> datetime | None:
    value = _read_optional_string(data, name)

    if value is None:
        return None

    normalized_value = f"{value[:-1]}+00:00" if value.endswith("Z") else value

    try:
        parsed_value = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None

    if parsed_value.tzinfo is None:
        return parsed_value.replace(tzinfo=local_timezone)

    return parsed_value.astimezone(local_timezone)


def _read_nested_object(
    data: dict[str, Any],
    *names: str,
) -> dict[str, Any] | None:
    current: Any = data

    for name in names:
        if not isinstance(current, dict):
            return None

        current = current.get(name)

    if not isinstance(current, dict):
        return None

    return current


def _read_community_day_bonus(value: Any) -> str | None:
    if not isinstance(value, list):
        return None

    for entry in value:
        if not isinstance(entry, dict):
            continue

        text = _read_optional_string(entry, "text")

        if text is None or text.casefold() == "increased spawns":
            continue

        return text

    return None


def _read_shiny_availability(
    value: Any,
    *,
    pokemon_name: str,
) -> bool | None:
    if not isinstance(value, list):
        return None

    normalized_name = pokemon_name.casefold()

    return any(
        isinstance(entry, dict)
        and isinstance(entry.get("name"), str)
        and entry["name"].strip().casefold() == normalized_name
        for entry in value
    )


def _read_optional_string(
    data: dict[str, Any],
    name: str,
) -> str | None:
    value = data.get(name)

    if not isinstance(value, str) or not value.strip():
        return None

    return value.strip()


def _read_optional_boolean(
    data: dict[str, Any],
    name: str,
) -> bool | None:
    value = data.get(name)

    if not isinstance(value, bool):
        return None

    return value
