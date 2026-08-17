from dataclasses import dataclass
from enum import StrEnum
from zoneinfo import ZoneInfo


class PokemonType(StrEnum):
    """Pokémon types supported by Novachrono."""

    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    ELECTRIC = "electric"
    GRASS = "grass"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


class RaidTier(StrEnum):
    """Raid tiers displayed by Novachrono."""

    FIVE_STAR = "five_star"
    MEGA = "mega"


class PokemonGoRegion(StrEnum):
    """Broad Pokémon GO regions needed for regional raid selection."""

    AMERICAS = "americas"
    EMEAI = "emeai"
    ASIA_PACIFIC = "asia_pacific"


@dataclass(frozen=True)
class CombatPowerRange:
    """Catch CP range for a raid boss."""

    minimum: int
    maximum: int


@dataclass(frozen=True)
class RaidBoss:
    """Normalized Pokémon GO raid boss."""

    name: str
    tier: RaidTier
    can_be_shiny: bool
    types: tuple[PokemonType, ...]
    normal_combat_power: CombatPowerRange
    boosted_combat_power: CombatPowerRange
    artwork_url: str | None = None


@dataclass(frozen=True)
class RaidRoster:
    """Current raid bosses relevant to the Novachrono display."""

    five_star: tuple[RaidBoss, ...]
    mega: tuple[RaidBoss, ...]


_LAKE_TRIO_REGIONS = {
    "uxie": PokemonGoRegion.ASIA_PACIFIC,
    "mesprit": PokemonGoRegion.EMEAI,
    "azelf": PokemonGoRegion.AMERICAS,
}


def infer_pokemon_go_region(timezone: ZoneInfo) -> PokemonGoRegion | None:
    """Infer a broad Pokémon GO region from an IANA timezone."""

    timezone_name = timezone.key

    if timezone_name.startswith(("Europe/", "Africa/")):
        return PokemonGoRegion.EMEAI

    if timezone_name in {"Asia/Kolkata", "Asia/Calcutta"}:
        return PokemonGoRegion.EMEAI

    if timezone_name.startswith("America/"):
        return PokemonGoRegion.AMERICAS

    if timezone_name.startswith(("Australia/", "Pacific/")):
        return PokemonGoRegion.ASIA_PACIFIC

    if timezone_name.startswith("Asia/"):
        return PokemonGoRegion.ASIA_PACIFIC

    return None


def select_regionally_relevant_raids(
    roster: RaidRoster,
    *,
    timezone: ZoneInfo,
) -> RaidRoster:
    """Filter known simultaneous regional raid groups when possible."""

    region = infer_pokemon_go_region(timezone)

    if region is None:
        return roster

    lake_trio_bosses = tuple(
        boss for boss in roster.five_star if _species_key(boss.name) in _LAKE_TRIO_REGIONS
    )

    # Do not filter an isolated Lake Trio boss. It might be globally
    # available as part of a special event.
    if len(lake_trio_bosses) < 2:
        return roster

    filtered_five_star = tuple(
        boss
        for boss in roster.five_star
        if _is_relevant_for_region(
            boss,
            region=region,
        )
    )

    return RaidRoster(
        five_star=filtered_five_star,
        mega=roster.mega,
    )


def _is_relevant_for_region(
    boss: RaidBoss,
    *,
    region: PokemonGoRegion,
) -> bool:
    species = _species_key(boss.name)
    required_region = _LAKE_TRIO_REGIONS.get(species)

    if required_region is None:
        return True

    return required_region is region


def _species_key(name: str) -> str:
    normalized_name = name.strip()

    if "(" in normalized_name:
        normalized_name = normalized_name.split("(", maxsplit=1)[0].strip()

    return normalized_name.casefold()
