import io
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoEventType,
    PokemonGoFeaturedPokemon,
)
from novachrono.sources.pokemon_artwork import (
    fetch_event_artwork,
)

BERLIN = ZoneInfo("Europe/Berlin")


def _create_schedule(
    *artwork_urls: str | None,
) -> EventSchedule:
    return EventSchedule(
        community_day=PokemonGoEvent(
            event_type=(PokemonGoEventType.COMMUNITY_DAY),
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
            featured_pokemon=tuple(
                PokemonGoFeaturedPokemon(
                    name=f"Pokemon {index}",
                    artwork_url=artwork_url,
                )
                for index, artwork_url in enumerate(artwork_urls)
            ),
        )
    )


def _create_response(
    data: bytes,
) -> MagicMock:
    response = MagicMock()
    response.read.return_value = data

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def _create_artwork_bytes() -> bytes:
    image = Image.new(
        mode="RGBA",
        size=(6, 6),
        color=(0, 0, 0, 0),
    )

    for x in (2, 3):
        for y in (2, 3):
            image.putpixel(
                (x, y),
                (255, 255, 255, 255),
            )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


@patch("novachrono.sources.pokemon_artwork.urlopen")
def test_fetch_event_artwork_loads_artwork(
    mocked_urlopen: MagicMock,
) -> None:
    artwork_url = "https://example.com/sobble.png"

    mocked_urlopen.return_value = _create_response(_create_artwork_bytes())

    artwork = fetch_event_artwork(_create_schedule(artwork_url))

    assert list(artwork) == [artwork_url]

    assert artwork[artwork_url].size == (2, 2)


@patch("novachrono.sources.pokemon_artwork.urlopen")
def test_fetch_event_artwork_loads_duplicate_url_once(
    mocked_urlopen: MagicMock,
) -> None:
    artwork_url = "https://example.com/shared.png"

    mocked_urlopen.return_value = _create_response(_create_artwork_bytes())

    fetch_event_artwork(
        _create_schedule(
            artwork_url,
            artwork_url,
        )
    )

    assert mocked_urlopen.call_count == 1


@patch("novachrono.sources.pokemon_artwork.urlopen")
def test_fetch_event_artwork_ignores_missing_url(
    mocked_urlopen: MagicMock,
) -> None:
    artwork = fetch_event_artwork(_create_schedule(None))

    assert artwork == {}

    mocked_urlopen.assert_not_called()


def test_fetch_event_artwork_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        fetch_event_artwork(
            _create_schedule(),
            timeout_seconds=0,
        )
