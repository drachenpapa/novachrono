from dataclasses import replace
from typing import Any, Final
from urllib.parse import quote, urlparse

from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoFeaturedPokemon,
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

POKEAPI_POKEMON_URL: Final = "https://pokeapi.co/api/v2/pokemon/{identifier}/"


def add_missing_event_artwork(
    schedule: EventSchedule,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> EventSchedule:
    """Fill missing event Pokémon artwork URLs using PokeAPI."""

    _validate_timeout(timeout_seconds)

    artwork_urls: dict[str, str | None] = {}

    def add_artwork(event: PokemonGoEvent | None) -> PokemonGoEvent | None:
        if event is None:
            return None

        featured_pokemon: list[PokemonGoFeaturedPokemon] = []

        for pokemon in event.featured_pokemon:
            if pokemon.artwork_url is not None:
                featured_pokemon.append(pokemon)
                continue

            if pokemon.name not in artwork_urls:
                try:
                    artwork_urls[pokemon.name] = fetch_pokemon_artwork_url(
                        pokemon.name, timeout_seconds=timeout_seconds
                    )
                except PokeApiError:
                    artwork_urls[pokemon.name] = None

            featured_pokemon.append(replace(pokemon, artwork_url=artwork_urls[pokemon.name]))

        return replace(event, featured_pokemon=tuple(featured_pokemon))

    return EventSchedule(
        community_day=add_artwork(schedule.community_day),
        community_day_classic=add_artwork(schedule.community_day_classic),
        spotlight_hour=add_artwork(schedule.spotlight_hour),
        max_monday=add_artwork(schedule.max_monday),
    )


def fetch_pokemon_artwork_url(
    name: str,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> str | None:
    """Retrieve an official Pokémon artwork URL from PokeAPI."""

    _validate_timeout(timeout_seconds)

    (species_name, _, _, regional_form) = _parse_display_name(name)

    identifier = _species_identifier(species_name)

    if regional_form is not None:
        form_suffix = _REGIONAL_FORMS[regional_form][0]

        identifier = f"{identifier}-{form_suffix}"

    response_data = _fetch_json(
        POKEAPI_POKEMON_URL.format(identifier=quote(identifier, safe="-")),
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(response_data, dict):
        raise PokeApiError("PokeAPI returned an unexpected response")

    return _read_official_artwork_url(response_data)


def _read_official_artwork_url(response_data: dict[str, Any]) -> str | None:
    sprites = response_data.get("sprites")

    if not isinstance(sprites, dict):
        return None

    other = sprites.get("other")

    if not isinstance(other, dict):
        return None

    official_artwork = other.get("official-artwork")

    if not isinstance(official_artwork, dict):
        return None

    artwork_url = official_artwork.get("front_default")

    if not isinstance(artwork_url, str) or not artwork_url.strip():
        return None

    normalized_url = artwork_url.strip()
    parsed_url = urlparse(normalized_url)

    if parsed_url.scheme.casefold() != "https" or parsed_url.hostname is None:
        return None

    return normalized_url
