"""ScrapedDuck Pokémon GO data-source adapters."""

from novachrono.sources.scraped_duck._common import DEFAULT_TIMEOUT_SECONDS, ScrapedDuckError
from novachrono.sources.scraped_duck.events import SCRAPED_DUCK_EVENTS_URL, fetch_event_schedule
from novachrono.sources.scraped_duck.raids import SCRAPED_DUCK_RAIDS_URL, fetch_raid_roster

__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "SCRAPED_DUCK_EVENTS_URL",
    "SCRAPED_DUCK_RAIDS_URL",
    "ScrapedDuckError",
    "fetch_event_schedule",
    "fetch_raid_roster",
]
