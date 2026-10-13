import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoEventType,
    PokemonGoFeaturedPokemon,
)
from novachrono.sources.pokeapi import (
    add_missing_event_artwork,
    fetch_pokemon_artwork_url,
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


def _create_artwork_response(
    artwork_url: str,
) -> MagicMock:
    return _create_response(
        {
            "sprites": {
                "other": {
                    "official-artwork": {
                        "front_default": artwork_url,
                    }
                }
            }
        }
    )


def _create_schedule(
    *pokemon: PokemonGoFeaturedPokemon,
) -> EventSchedule:
    return EventSchedule(
        community_day=PokemonGoEvent(
            event_type=PokemonGoEventType.COMMUNITY_DAY,
            name="Test Community Day",
            start=datetime(
                2026,
                10,
                10,
                14,
                tzinfo=BERLIN,
            ),
            end=datetime(
                2026,
                10,
                10,
                17,
                tzinfo=BERLIN,
            ),
            featured_pokemon=pokemon,
        )
    )


@patch("novachrono.sources.pokeapi._common.urlopen")
def test_fetch_pokemon_artwork_url_uses_regional_form_identifier(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_artwork_response(
        "https://example.com/alola-sandshrew.png"
    )

    artwork_url = fetch_pokemon_artwork_url("Sandshrew (Alolan)")

    assert artwork_url == "https://example.com/alola-sandshrew.png"

    request = mocked_urlopen.call_args.args[0]

    assert "/pokemon/sandshrew-alola/" in request.full_url


@patch("novachrono.sources.pokeapi._common.urlopen")
def test_add_missing_event_artwork_fills_missing_url(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_artwork_response("https://example.com/sobble.png")

    schedule = _create_schedule(PokemonGoFeaturedPokemon(name="Sobble"))

    enriched = add_missing_event_artwork(schedule)

    assert enriched.community_day is not None

    assert (
        enriched.community_day.featured_pokemon[0].artwork_url == "https://example.com/sobble.png"
    )


@patch("novachrono.sources.pokeapi._common.urlopen")
def test_add_missing_event_artwork_preserves_existing_url(
    mocked_urlopen: MagicMock,
) -> None:
    schedule = _create_schedule(
        PokemonGoFeaturedPokemon(
            name="Sobble",
            artwork_url="https://example.com/existing.png",
        )
    )

    enriched = add_missing_event_artwork(schedule)

    assert enriched == schedule

    mocked_urlopen.assert_not_called()


@patch("novachrono.sources.pokeapi._common.urlopen")
def test_add_missing_event_artwork_caches_duplicate_names(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_artwork_response("https://example.com/sobble.png")

    schedule = _create_schedule(
        PokemonGoFeaturedPokemon(name="Sobble"),
        PokemonGoFeaturedPokemon(name="Sobble"),
    )

    add_missing_event_artwork(schedule)

    assert mocked_urlopen.call_count == 1
