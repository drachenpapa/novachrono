from datetime import datetime, tzinfo
from typing import Any, Final

from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoEventType,
)
from novachrono.sources.scraped_duck._common import (
    DEFAULT_TIMEOUT_SECONDS,
    _fetch_entries,
    _validate_timeout,
)
from novachrono.sources.scraped_duck._event_parser import (
    _deduplicate_featured_pokemon,
    _parse_event,
    _parse_event_type,
)

SCRAPED_DUCK_EVENTS_URL: Final = (
    "https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/events.json"
)


def fetch_event_schedule(
    *,
    now: datetime,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> EventSchedule:
    """Retrieve the current or next supported Pokémon GO events."""

    _validate_timeout(timeout_seconds)
    local_timezone = now.tzinfo

    if local_timezone is None or now.utcoffset() is None:
        raise ValueError("Pokémon GO event reference time must be timezone-aware")

    return _parse_event_schedule(
        _fetch_entries(SCRAPED_DUCK_EVENTS_URL, timeout_seconds=timeout_seconds),
        now=now,
        local_timezone=local_timezone,
    )


def _parse_event_schedule(
    entries: list[Any],
    *,
    now: datetime,
    local_timezone: tzinfo,
) -> EventSchedule:
    events_by_type: dict[PokemonGoEventType, list[PokemonGoEvent]] = {
        event_type: [] for event_type in PokemonGoEventType
    }

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        event_type = _parse_event_type(entry)

        if event_type is None:
            continue

        event = _parse_event(entry, event_type=event_type, local_timezone=local_timezone)

        if event is None:
            continue

        if event.end <= now:
            continue

        events_by_type[event_type].append(event)

    return EventSchedule(
        community_day=_select_event_occurrence(events_by_type[PokemonGoEventType.COMMUNITY_DAY]),
        community_day_classic=_select_event_occurrence(
            events_by_type[PokemonGoEventType.COMMUNITY_DAY_CLASSIC]
        ),
        spotlight_hour=_select_event_occurrence(events_by_type[PokemonGoEventType.SPOTLIGHT_HOUR]),
        max_monday=_select_event_occurrence(events_by_type[PokemonGoEventType.MAX_MONDAY]),
    )


def _select_event_occurrence(events: list[PokemonGoEvent]) -> PokemonGoEvent | None:
    if not events:
        return None

    first_event = min(events, key=lambda event: event.start)

    matching_events = [
        event
        for event in events
        if (event.start == first_event.start and event.end == first_event.end)
    ]

    return _merge_events(matching_events)


def _merge_events(events: list[PokemonGoEvent]) -> PokemonGoEvent:
    first_event = events[0]
    featured_pokemon = _deduplicate_featured_pokemon(
        [featured for event in events for featured in event.featured_pokemon]
    )
    bonus = next((event.bonus for event in events if event.bonus is not None), None)

    return PokemonGoEvent(
        event_type=first_event.event_type,
        name=first_event.name,
        start=first_event.start,
        end=first_event.end,
        featured_pokemon=featured_pokemon,
        bonus=bonus,
    )
