from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RaidTier(StrEnum):
    """Raid tiers displayed by Novachrono."""

    FIVE_STAR = "five_star"
    SHADOW_FIVE_STAR = "shadow_five_star"
    MEGA = "mega"


class PokemonGoEventType(StrEnum):
    """Pokémon GO event categories displayed by Novachrono."""

    COMMUNITY_DAY = "community_day"
    COMMUNITY_DAY_CLASSIC = "community_day_classic"
    SPOTLIGHT_HOUR = "spotlight_hour"
    MAX_MONDAY = "max_monday"


@dataclass(frozen=True)
class RaidBoss:
    """Normalized Pokémon GO raid boss."""

    name: str
    can_be_shiny: bool
    artwork_url: str | None = None


@dataclass(frozen=True)
class RaidRoster:
    """Current raid bosses relevant to the Novachrono display."""

    five_star: tuple[RaidBoss, ...]
    mega: tuple[RaidBoss, ...]
    shadow_five_star: tuple[RaidBoss, ...] = ()


@dataclass(frozen=True)
class PokemonGoFeaturedPokemon:
    """Pokémon featured by a Pokémon GO event."""

    name: str
    can_be_shiny: bool | None = None
    artwork_url: str | None = None


@dataclass(frozen=True)
class PokemonGoEvent:
    """Normalized Pokémon GO event relevant to the display."""

    event_type: PokemonGoEventType
    name: str
    start: datetime
    end: datetime
    featured_pokemon: tuple[PokemonGoFeaturedPokemon, ...] = ()
    bonus: str | None = None


@dataclass(frozen=True)
class EventSchedule:
    """Current or next event for each supported Pokémon GO category."""

    community_day: PokemonGoEvent | None = None
    community_day_classic: PokemonGoEvent | None = None
    spotlight_hour: PokemonGoEvent | None = None
    max_monday: PokemonGoEvent | None = None
