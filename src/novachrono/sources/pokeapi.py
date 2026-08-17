import json
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from novachrono.pokemon_go import RaidBoss, RaidRoster

POKEAPI_SPECIES_URL: Final = "https://pokeapi.co/api/v2/pokemon-species/{identifier}/"
DEFAULT_TIMEOUT_SECONDS: Final = 8.0

_LOCALE_LANGUAGE_CODES: Final = {
    "de_DE": "de",
    "en_US": "en",
}


class PokeApiError(RuntimeError):
    """Raised when localized Pokémon data cannot be retrieved."""


def localize_raid_roster(
    roster: RaidRoster,
    *,
    locale: str,
) -> RaidRoster:
    """Return a raid roster with localized Pokémon names.

    Localization is best-effort. If PokeAPI is unavailable or a Pokémon
    cannot be resolved, the original ScrapedDuck name is retained.
    """

    if locale == "en_US":
        return roster

    localized_names: dict[str, str] = {}

    def localize_boss(boss: RaidBoss) -> RaidBoss:
        if boss.name not in localized_names:
            try:
                localized_names[boss.name] = fetch_localized_pokemon_name(
                    boss.name,
                    locale=locale,
                )
            except PokeApiError:
                localized_names[boss.name] = boss.name

        return RaidBoss(
            name=localized_names[boss.name],
            tier=boss.tier,
            can_be_shiny=boss.can_be_shiny,
            types=boss.types,
            normal_combat_power=boss.normal_combat_power,
            boosted_combat_power=boss.boosted_combat_power,
            artwork_url=boss.artwork_url,
        )

    return RaidRoster(
        five_star=tuple(localize_boss(boss) for boss in roster.five_star),
        mega=tuple(localize_boss(boss) for boss in roster.mega),
    )


def fetch_localized_pokemon_name(
    name: str,
    *,
    locale: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Retrieve a localized Pokémon species name from PokeAPI."""

    if timeout_seconds <= 0:
        raise ValueError("PokeAPI timeout must be greater than zero")

    language_code = _LOCALE_LANGUAGE_CODES.get(locale)

    if language_code is None:
        return name

    species_name, is_mega, mega_form = _parse_display_name(name)
    identifier = _species_identifier(species_name)

    url = POKEAPI_SPECIES_URL.format(identifier=quote(identifier, safe="-"))

    request = Request(
        url=url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Novachrono",
        },
        method="GET",
    )

    try:
        with urlopen(  # nosec B310 - fixed PokeAPI HTTPS endpoint
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise PokeApiError(f"PokeAPI returned HTTP {error.code}: {error.reason}") from error
    except URLError as error:
        raise PokeApiError(f"Could not reach PokeAPI: {error.reason}") from error
    except TimeoutError as error:
        raise PokeApiError("Connection to PokeAPI timed out") from error

    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise PokeApiError("PokeAPI returned invalid JSON") from error

    if not isinstance(response_data, dict):
        raise PokeApiError("PokeAPI returned an unexpected response")

    localized_name = _read_localized_name(
        response_data,
        language_code=language_code,
    )

    if localized_name is None:
        return name

    if not is_mega:
        return localized_name

    prefix = f"Mega-{localized_name}" if locale == "de_DE" else f"Mega {localized_name}"

    if mega_form:
        return f"{prefix} {mega_form}"

    return prefix


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


def _parse_display_name(name: str) -> tuple[str, bool, str | None]:
    normalized_name = name.strip()

    is_mega = False
    mega_form: str | None = None

    if normalized_name.casefold().startswith(("mega ", "mega-")):
        is_mega = True
        normalized_name = normalized_name[5:].strip()

    if is_mega and normalized_name.endswith((" X", " Y")):
        mega_form = normalized_name[-1]
        normalized_name = normalized_name[:-2].strip()

    if "(" in normalized_name:
        normalized_name = normalized_name.split("(", maxsplit=1)[0].strip()

    return normalized_name, is_mega, mega_form


def _species_identifier(name: str) -> str:
    return name.casefold().replace("'", "").replace("\u2019", "").replace(".", "").replace(" ", "-")
