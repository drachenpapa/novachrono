import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from novachrono.models.pokemon_go import PokemonGoEventType
from novachrono.sources.scraped_duck import (
    ScrapedDuckError,
    fetch_event_schedule,
)

BERLIN = ZoneInfo("Europe/Berlin")


def _create_response(
    payload: object,
) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def _create_event(
    *,
    name: str,
    event_type: str,
    start: str,
    end: str,
    extra_data: dict[str, object] | None = None,
    heading: str | None = None,
) -> dict[str, object]:
    event: dict[str, object] = {
        "name": name,
        "eventType": event_type,
        "start": start,
        "end": end,
    }

    if extra_data is not None:
        event["extraData"] = extra_data

    if heading is not None:
        event["heading"] = heading

    return event


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_parses_supported_events(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Zorua Community Day",
                event_type="community-day",
                start="2026-10-10T14:00:00",
                end="2026-10-10T17:00:00",
                extra_data={
                    "communityday": {
                        "spawns": [
                            {
                                "name": "Zorua",
                                "image": "https://example.com/zorua.png",
                            }
                        ],
                        "shinies": [
                            {
                                "name": "Zorua",
                            }
                        ],
                        "bonuses": [
                            {
                                "text": "Increased Spawns",
                            },
                            {
                                "text": "3\u00d7 Catch XP",
                            },
                        ],
                    }
                },
            ),
            _create_event(
                name="Rattata Spotlight Hour",
                event_type="pokemon-spotlight-hour",
                start="2026-09-24T18:00:00",
                end="2026-09-24T19:00:00",
                extra_data={
                    "spotlight": {
                        "name": "Rattata",
                        "canBeShiny": True,
                        "image": "https://example.com/rattata.png",
                        "bonus": "2\u00d7 Evolution XP",
                    }
                },
            ),
            _create_event(
                name="Dynamax Sobble during Max Monday",
                event_type="max-mondays",
                start="2026-09-28T06:00:00",
                end="2026-09-28T21:00:00",
            ),
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            9,
            22,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.community_day is not None
    assert schedule.community_day.event_type is PokemonGoEventType.COMMUNITY_DAY
    assert schedule.community_day.featured_pokemon[0].name == "Zorua"
    assert schedule.community_day.bonus == "3\u00d7 Catch XP"

    assert schedule.spotlight_hour is not None
    assert schedule.spotlight_hour.featured_pokemon[0].name == "Rattata"

    assert schedule.max_monday is not None
    assert schedule.max_monday.featured_pokemon[0].name == "Sobble"


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_detects_community_day_classic(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Bulbasaur Community Day Classic",
                event_type="community-day",
                start="2026-10-17T14:00:00",
                end="2026-10-17T17:00:00",
            )
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.community_day is None

    assert schedule.community_day_classic is not None
    assert schedule.community_day_classic.event_type is PokemonGoEventType.COMMUNITY_DAY_CLASSIC
    assert schedule.community_day_classic.featured_pokemon[0].name == "Bulbasaur"


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_keeps_unannounced_community_day_without_pokemon(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="November Community Day",
                event_type="community-day",
                start="2026-11-21T14:00:00",
                end="2026-11-21T17:00:00",
            )
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            13,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.community_day is not None
    assert schedule.community_day.name == "November Community Day"
    assert schedule.community_day.featured_pokemon == ()


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_preserves_multiple_community_day_pokemon(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Sandshrew Community Day",
                event_type="community-day",
                start="2026-10-10T14:00:00",
                end="2026-10-10T17:00:00",
                extra_data={
                    "communityday": {
                        "spawns": [
                            {
                                "name": "Sandshrew",
                            },
                            {
                                "name": "Sandshrew (Alolan)",
                            },
                        ]
                    }
                },
            )
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.community_day is not None

    assert [pokemon.name for pokemon in schedule.community_day.featured_pokemon] == [
        "Sandshrew",
        "Sandshrew (Alolan)",
    ]


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_merges_same_max_monday_occurrence(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Dynamax Articuno during Max Monday",
                event_type="max-mondays",
                start="2026-10-05T06:00:00",
                end="2026-10-05T21:00:00",
            ),
            _create_event(
                name="Dynamax Zapdos during Max Monday",
                event_type="max-mondays",
                start="2026-10-05T06:00:00",
                end="2026-10-05T21:00:00",
            ),
            _create_event(
                name="Dynamax Moltres during Max Monday",
                event_type="max-mondays",
                start="2026-10-05T06:00:00",
                end="2026-10-05T21:00:00",
            ),
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.max_monday is not None

    assert [pokemon.name for pokemon in schedule.max_monday.featured_pokemon] == [
        "Articuno",
        "Zapdos",
        "Moltres",
    ]


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_parses_combined_max_monday_names(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name=("Dynamax Articuno, Dynamax Zapdos, and Dynamax Moltres during Max Monday"),
                event_type="max-mondays",
                start="2026-10-05T06:00:00",
                end="2026-10-05T21:00:00",
            )
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.max_monday is not None

    assert [pokemon.name for pokemon in schedule.max_monday.featured_pokemon] == [
        "Articuno",
        "Zapdos",
        "Moltres",
    ]


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_prefers_active_event(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Active Spotlight Hour",
                event_type="pokemon-spotlight-hour",
                start="2026-10-01T18:00:00",
                end="2026-10-01T19:00:00",
            ),
            _create_event(
                name="Future Spotlight Hour",
                event_type="pokemon-spotlight-hour",
                start="2026-10-08T18:00:00",
                end="2026-10-08T19:00:00",
            ),
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            18,
            30,
            tzinfo=BERLIN,
        )
    )

    assert schedule.spotlight_hour is not None
    assert schedule.spotlight_hour.name == "Active Spotlight Hour"


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_ignores_finished_events(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Old Spotlight Hour",
                event_type="pokemon-spotlight-hour",
                start="2026-09-24T18:00:00",
                end="2026-09-24T19:00:00",
            ),
            _create_event(
                name="Next Spotlight Hour",
                event_type="pokemon-spotlight-hour",
                start="2026-10-08T18:00:00",
                end="2026-10-08T19:00:00",
            ),
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.spotlight_hour is not None
    assert schedule.spotlight_hour.name == "Next Spotlight Hour"


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_converts_utc_time(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Test Spotlight Hour",
                event_type="pokemon-spotlight-hour",
                start="2026-10-01T16:00:00Z",
                end="2026-10-01T17:00:00Z",
            )
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.spotlight_hour is not None
    assert schedule.spotlight_hour.start.hour == 18
    assert schedule.spotlight_hour.end.hour == 19


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_ignores_unsupported_events(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Some Other Event",
                event_type="other-event",
                start="not-a-date",
                end="also-not-a-date",
            )
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.community_day is None
    assert schedule.community_day_classic is None
    assert schedule.spotlight_hour is None
    assert schedule.max_monday is None


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_ignores_supported_event_with_invalid_datetime(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Unknown Community Day",
                event_type="community-day",
                start="TBD",
                end="TBD",
            ),
            _create_event(
                name="Bulbasaur Community Day",
                event_type="community-day",
                start="2026-10-17T14:00:00",
                end="2026-10-17T17:00:00",
            ),
        ]
    )

    schedule = fetch_event_schedule(
        now=datetime(
            2026,
            10,
            1,
            12,
            tzinfo=BERLIN,
        )
    )

    assert schedule.community_day is not None
    assert schedule.community_day.name == "Bulbasaur Community Day"


def test_fetch_event_schedule_requires_timezone_aware_now() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        fetch_event_schedule(
            now=datetime(
                2026,
                10,
                1,
                12,
            )
        )


def test_fetch_event_schedule_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        fetch_event_schedule(
            now=datetime(
                2026,
                10,
                1,
                12,
                tzinfo=BERLIN,
            ),
            timeout_seconds=0,
        )


@patch("novachrono.sources.scraped_duck._common.urlopen")
def test_fetch_event_schedule_rejects_invalid_time_range(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_event(
                name="Invalid Event",
                event_type="community-day",
                start="2026-10-10T17:00:00",
                end="2026-10-10T14:00:00",
            )
        ]
    )

    with pytest.raises(
        ScrapedDuckError,
        match="invalid time range",
    ):
        fetch_event_schedule(
            now=datetime(
                2026,
                10,
                1,
                12,
                tzinfo=BERLIN,
            )
        )
