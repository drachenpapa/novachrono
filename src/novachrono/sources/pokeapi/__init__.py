"""PokeAPI Pokémon metadata adapters."""

from novachrono.sources.pokeapi._common import (
    DEFAULT_TIMEOUT_SECONDS,
    PokeApiError,
)
from novachrono.sources.pokeapi.artwork import (
    POKEAPI_POKEMON_URL,
    add_missing_event_artwork,
    fetch_pokemon_artwork_url,
)
from novachrono.sources.pokeapi.localization import (
    POKEAPI_SPECIES_URL,
    fetch_localized_pokemon_name,
    localize_event_schedule,
    localize_raid_roster,
)

__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "POKEAPI_POKEMON_URL",
    "POKEAPI_SPECIES_URL",
    "PokeApiError",
    "add_missing_event_artwork",
    "fetch_localized_pokemon_name",
    "fetch_pokemon_artwork_url",
    "localize_event_schedule",
    "localize_raid_roster",
]
