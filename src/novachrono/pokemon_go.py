from dataclasses import dataclass
from enum import StrEnum


class RaidTier(StrEnum):
    """Raid tiers displayed by Novachrono."""

    FIVE_STAR = "five_star"
    MEGA = "mega"


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
