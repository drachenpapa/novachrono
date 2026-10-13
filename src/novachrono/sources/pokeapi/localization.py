from dataclasses import replace
from typing import Any, Final
from urllib.parse import quote

from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    RaidBoss,
    RaidRoster,
)
from novachrono.sources.pokeapi._common import (
    _REGIONAL_FORMS,
    DEFAULT_TIMEOUT_SECONDS,
    PokeApiError,
    _fetch_json,
    _parse_display_name,
    _species_identifier,
    _validate_timeout,
)

POKEAPI_SPECIES_URL: Final = "https://pokeapi.co/api/v2/pokemon-species/{identifier}/"

_LOCALE_LANGUAGE_CODES: Final = {
    "de_DE": "de",
    "en_US": "en",
}


def localize_raid_roster(
    roster: RaidRoster,
    *,
    locale: str,
) -> RaidRoster:
    """Return a raid roster with localized Pokémon names."""

    if locale == "en_US":
        return roster

    localized_names: dict[str, str] = {}

    def localize_boss(boss: RaidBoss) -> RaidBoss:
        return replace(
            boss,
            name=_localize_name_best_effort(
                boss.name, locale=locale, localized_names=localized_names
            ),
        )

    return RaidRoster(
        five_star=tuple(localize_boss(boss) for boss in roster.five_star),
        mega=tuple(localize_boss(boss) for boss in roster.mega),
        shadow_five_star=tuple(localize_boss(boss) for boss in roster.shadow_five_star),
    )


def localize_event_schedule(
    schedule: EventSchedule,
    *,
    locale: str,
) -> EventSchedule:
    """Return an event schedule with localized featured Pokémon names."""

    if locale == "en_US":
        return schedule

    localized_names: dict[str, str] = {}

    def localize_event(event: PokemonGoEvent | None) -> PokemonGoEvent | None:
        if event is None:
            return None

        return replace(
            event,
            featured_pokemon=tuple(
                replace(
                    pokemon,
                    name=_localize_name_best_effort(
                        pokemon.name, locale=locale, localized_names=localized_names
                    ),
                )
                for pokemon in event.featured_pokemon
            ),
        )

    return EventSchedule(
        community_day=localize_event(schedule.community_day),
        community_day_classic=localize_event(schedule.community_day_classic),
        spotlight_hour=localize_event(schedule.spotlight_hour),
        max_monday=localize_event(schedule.max_monday),
    )


def fetch_localized_pokemon_name(
    name: str,
    *,
    locale: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Retrieve a localized Pokémon species name from PokeAPI."""

    _validate_timeout(timeout_seconds)

    language_code = _LOCALE_LANGUAGE_CODES.get(locale)

    if language_code is None:
        return name

    (
        species_name,
        is_mega,
        mega_form,
        regional_form,
    ) = _parse_display_name(name)

    identifier = _species_identifier(species_name)

    response_data = _fetch_json(
        POKEAPI_SPECIES_URL.format(identifier=quote(identifier, safe="-")),
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(response_data, dict):
        raise PokeApiError("PokeAPI returned an unexpected response")

    localized_name = _read_localized_name(response_data, language_code=language_code)

    if localized_name is None:
        return name

    if regional_form is not None:
        localized_name = _regional_display_name(
            localized_name,
            regional_form=regional_form,
            locale=locale,
        )

    if not is_mega:
        return localized_name

    prefix = f"Mega-{localized_name}" if locale == "de_DE" else f"Mega {localized_name}"

    if mega_form is not None:
        return f"{prefix} {mega_form}"

    return prefix


def _localize_name_best_effort(
    name: str,
    *,
    locale: str,
    localized_names: dict[str, str],
) -> str:
    if name not in localized_names:
        try:
            localized_names[name] = fetch_localized_pokemon_name(name, locale=locale)
        except PokeApiError:
            localized_names[name] = name

    return localized_names[name]


def _read_localized_name(
    response_data: dict[str, Any],
    *,
    language_code: str,
) -> str | None:
    names = response_data.get("names")

    if not isinstance(names, list):
        raise PokeApiError("PokeAPI response contains invalid 'names'")

    for entry in names:
        if not isinstance(entry, dict):
            continue

        language = entry.get("language")

        if not isinstance(language, dict):
            continue

        if language.get("name") != language_code:
            continue

        localized_name = entry.get("name")

        if isinstance(localized_name, str) and localized_name.strip():
            return localized_name.strip()

    return None


def _regional_display_name(
    localized_name: str,
    *,
    regional_form: str,
    locale: str,
) -> str:
    _, region_name = _REGIONAL_FORMS[regional_form]

    if locale == "de_DE":
        return f"{region_name}-{localized_name}"

    adjective = regional_form.capitalize()

    return f"{adjective} {localized_name}"
