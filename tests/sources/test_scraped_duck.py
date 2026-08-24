import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from novachrono.pokemon_go import RaidBoss
from novachrono.sources.scraped_duck import (
    ScrapedDuckError,
    fetch_raid_roster,
)


def _create_response(
    payload: object,
) -> MagicMock:
    return _create_raw_response(json.dumps(payload))


def _create_raw_response(
    body: str,
) -> MagicMock:
    return _create_bytes_response(body.encode("utf-8"))


def _create_bytes_response(
    body: bytes,
) -> MagicMock:
    response = MagicMock()
    response.read.return_value = body

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def _create_raid(
    *,
    name: str,
    tier: str,
    shiny: bool = True,
    image_url: str = "https://example.com/artwork.png",
) -> dict[str, object]:
    return {
        "name": name,
        "tier": tier,
        "canBeShiny": shiny,
        "image": image_url,
    }


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_normalizes_relevant_raids(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_raid(
                name="Zacian (Crowned Sword)",
                tier="5-Star Raids",
                image_url="https://example.com/zacian.png",
            ),
            _create_raid(
                name="Mega Gengar",
                tier="Mega Raids",
                image_url="https://example.com/mega-gengar.png",
            ),
            _create_raid(
                name="Ralts",
                tier="1-Star Raids",
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert roster.five_star == (
        RaidBoss(
            name="Zacian (Crowned Sword)",
            can_be_shiny=True,
            artwork_url="https://example.com/zacian.png",
        ),
    )

    assert roster.mega == (
        RaidBoss(
            name="Mega Gengar",
            can_be_shiny=True,
            artwork_url="https://example.com/mega-gengar.png",
        ),
    )


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_ignores_shadow_five_star_raids(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_raid(
                name="Uxie",
                tier="5-Star Raids",
            ),
            _create_raid(
                name="Mesprit",
                tier="5-Star Raids",
            ),
            _create_raid(
                name="Azelf",
                tier="5-Star Raids",
            ),
            _create_raid(
                name="Shadow Giratina",
                tier="5-Star Raids",
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert [boss.name for boss in roster.five_star] == [
        "Uxie",
        "Mesprit",
        "Azelf",
    ]


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_rejects_insecure_artwork_url(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_raid(
                name="Zacian",
                tier="5-Star Raids",
                image_url="http://example.com/zacian.png",
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert roster.five_star[0].artwork_url is None


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_preserves_multiple_bosses(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_raid(
                name="Zacian",
                tier="5-Star Raids",
            ),
            _create_raid(
                name="Zamazenta",
                tier="5-Star Raids",
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert [boss.name for boss in roster.five_star] == [
        "Zacian",
        "Zamazenta",
    ]


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_accepts_legacy_tier_names(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_raid(
                name="Five Star",
                tier="Tier 5",
            ),
            _create_raid(
                name="Mega Boss",
                tier="Mega",
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert len(roster.five_star) == 1
    assert len(roster.mega) == 1


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_ignores_other_tiers(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            _create_raid(
                name="Tier One",
                tier="1-Star Raids",
            ),
            _create_raid(
                name="Tier Three",
                tier="3-Star Raids",
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert roster.five_star == ()
    assert roster.mega == ()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_rejects_invalid_relevant_boss(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            {
                "name": "Zacian",
                "tier": "5-Star Raids",
                "image": "https://example.com/zacian.png",
            }
        ]
    )

    with pytest.raises(
        ScrapedDuckError,
        match="canBeShiny",
    ):
        fetch_raid_roster()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_reports_connection_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = URLError("Connection refused")

    with pytest.raises(
        ScrapedDuckError,
        match="Could not reach ScrapedDuck",
    ):
        fetch_raid_roster()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_reports_http_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = HTTPError(
        url="https://example.com",
        code=503,
        msg="Service Unavailable",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )

    with pytest.raises(
        ScrapedDuckError,
        match="ScrapedDuck returned HTTP 503",
    ):
        fetch_raid_roster()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_reports_timeout(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = TimeoutError()

    with pytest.raises(
        ScrapedDuckError,
        match="timed out",
    ):
        fetch_raid_roster()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_rejects_invalid_utf8(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_bytes_response(b"\xff")

    with pytest.raises(
        ScrapedDuckError,
        match="invalid UTF-8 response",
    ):
        fetch_raid_roster()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_rejects_invalid_json(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_raw_response("not-json")

    with pytest.raises(
        ScrapedDuckError,
        match="invalid JSON",
    ):
        fetch_raid_roster()


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_rejects_non_list_response(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "unexpected": "object",
        }
    )

    with pytest.raises(
        ScrapedDuckError,
        match="unexpected response",
    ):
        fetch_raid_roster()


def test_fetch_raid_roster_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        fetch_raid_roster(
            timeout_seconds=0,
        )
