import io
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest
from PIL import Image

from novachrono.pokemon_go import RaidBoss, RaidRoster
from novachrono.sources.pokemon_artwork import fetch_raid_artwork


def test_fetch_raid_artwork_loads_and_trims_artwork() -> None:
    artwork_url = "https://example.com/vesprit.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url=artwork_url,
            ),
        ),
        mega=(),
    )

    with patch("novachrono.sources.pokemon_artwork.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value = _create_response(_create_artwork_bytes())

        artwork_by_url = fetch_raid_artwork(roster)

    assert list(artwork_by_url) == [artwork_url]
    assert artwork_by_url[artwork_url].mode == "RGBA"
    assert artwork_by_url[artwork_url].size == (2, 2)


def test_fetch_raid_artwork_loads_duplicate_url_only_once() -> None:
    artwork_url = "https://example.com/shared.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url=artwork_url,
            ),
        ),
        mega=(
            _create_boss(
                artwork_url=artwork_url,
            ),
        ),
    )

    with patch("novachrono.sources.pokemon_artwork.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value = _create_response(_create_artwork_bytes())

        fetch_raid_artwork(roster)

    assert mocked_urlopen.call_count == 1


def test_fetch_raid_artwork_ignores_missing_url() -> None:
    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url=None,
            ),
        ),
        mega=(),
    )

    with patch("novachrono.sources.pokemon_artwork.urlopen") as mocked_urlopen:
        artwork_by_url = fetch_raid_artwork(roster)

    assert artwork_by_url == {}
    mocked_urlopen.assert_not_called()


def test_fetch_raid_artwork_ignores_insecure_url() -> None:
    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url="http://example.com/vesprit.png",
            ),
        ),
        mega=(),
    )

    with patch("novachrono.sources.pokemon_artwork.urlopen") as mocked_urlopen:
        artwork_by_url = fetch_raid_artwork(roster)

    assert artwork_by_url == {}
    mocked_urlopen.assert_not_called()


def test_fetch_raid_artwork_ignores_connection_error() -> None:
    artwork_url = "https://example.com/vesprit.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url=artwork_url,
            ),
        ),
        mega=(),
    )

    with patch(
        "novachrono.sources.pokemon_artwork.urlopen",
        side_effect=URLError("Connection refused"),
    ):
        artwork_by_url = fetch_raid_artwork(roster)

    assert artwork_by_url == {}


def test_fetch_raid_artwork_ignores_timeout() -> None:
    artwork_url = "https://example.com/vesprit.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url=artwork_url,
            ),
        ),
        mega=(),
    )

    with patch(
        "novachrono.sources.pokemon_artwork.urlopen",
        side_effect=TimeoutError(),
    ):
        artwork_by_url = fetch_raid_artwork(roster)

    assert artwork_by_url == {}


def test_fetch_raid_artwork_ignores_invalid_image() -> None:
    artwork_url = "https://example.com/vesprit.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                artwork_url=artwork_url,
            ),
        ),
        mega=(),
    )

    with patch("novachrono.sources.pokemon_artwork.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value = _create_response(b"not-an-image")

        artwork_by_url = fetch_raid_artwork(roster)

    assert artwork_by_url == {}


def test_fetch_raid_artwork_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        fetch_raid_artwork(
            RaidRoster(
                five_star=(),
                mega=(),
            ),
            timeout_seconds=0,
        )


def _create_response(data: bytes) -> MagicMock:
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
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def _create_boss(
    *,
    artwork_url: str | None,
) -> RaidBoss:
    return RaidBoss(
        name="Test Boss",
        can_be_shiny=True,
        artwork_url=artwork_url,
    )
