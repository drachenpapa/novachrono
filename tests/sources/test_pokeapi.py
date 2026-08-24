import json
from unittest.mock import MagicMock, patch

import pytest

from novachrono.pokemon_go import RaidBoss, RaidRoster
from novachrono.sources.pokeapi import (
    PokeApiError,
    fetch_localized_pokemon_name,
    localize_raid_roster,
)


def _create_response(localized_name: str) -> MagicMock:
    return _create_raw_response(
        json.dumps(
            {
                "names": [
                    {
                        "language": {
                            "name": "en",
                        },
                        "name": "English Name",
                    },
                    {
                        "language": {
                            "name": "de",
                        },
                        "name": localized_name,
                    },
                ]
            }
        )
    )


def _create_raw_response(body: str) -> MagicMock:
    return _create_bytes_response(body.encode("utf-8"))


def _create_bytes_response(body: bytes) -> MagicMock:
    response = MagicMock()
    response.read.return_value = body

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


@patch("novachrono.sources.pokeapi.urlopen")
def test_fetch_localized_pokemon_name_returns_german_name(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response("Selfe")

    name = fetch_localized_pokemon_name(
        "Uxie",
        locale="de_DE",
    )

    assert name == "Selfe"

    request = mocked_urlopen.call_args.args[0]

    assert "/pokemon-species/uxie/" in request.full_url


@patch("novachrono.sources.pokeapi.urlopen")
def test_fetch_localized_mega_name(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response("Lohgock")

    name = fetch_localized_pokemon_name(
        "Mega Blaziken",
        locale="de_DE",
    )

    assert name == "Mega-Lohgock"

    request = mocked_urlopen.call_args.args[0]

    assert "/pokemon-species/blaziken/" in request.full_url


@patch("novachrono.sources.pokeapi.urlopen")
def test_fetch_localized_mega_form_name(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response("Glurak")

    name = fetch_localized_pokemon_name(
        "Mega Charizard X",
        locale="de_DE",
    )

    assert name == "Mega-Glurak X"

    request = mocked_urlopen.call_args.args[0]

    assert "/pokemon-species/charizard/" in request.full_url


@patch("novachrono.sources.pokeapi.urlopen")
def test_localize_raid_roster_keeps_english_without_request(
    mocked_urlopen: MagicMock,
) -> None:
    roster = _create_roster(
        five_star_name="Mesprit",
        mega_name="Mega Blaziken",
    )

    localized = localize_raid_roster(
        roster,
        locale="en_US",
    )

    assert localized == roster
    mocked_urlopen.assert_not_called()


@patch("novachrono.sources.pokeapi.urlopen")
def test_localize_raid_roster_preserves_boss_data(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = [
        _create_response("Vesprit"),
        _create_response("Lohgock"),
    ]

    roster = _create_roster(
        five_star_name="Mesprit",
        mega_name="Mega Blaziken",
    )

    localized = localize_raid_roster(
        roster,
        locale="de_DE",
    )

    assert localized.five_star[0] == RaidBoss(
        name="Vesprit",
        can_be_shiny=True,
        artwork_url="https://example.com/mesprit.png",
    )

    assert localized.mega[0] == RaidBoss(
        name="Mega-Lohgock",
        can_be_shiny=True,
        artwork_url="https://example.com/mega-blaziken.png",
    )


@patch("novachrono.sources.pokeapi.urlopen")
def test_localize_raid_roster_falls_back_when_api_fails(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = TimeoutError()

    roster = _create_roster(
        five_star_name="Mesprit",
        mega_name="Mega Blaziken",
    )

    localized = localize_raid_roster(
        roster,
        locale="de_DE",
    )

    assert localized == roster


@patch("novachrono.sources.pokeapi.urlopen")
def test_invalid_utf8_raises_poke_api_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_bytes_response(b"\xff")

    with pytest.raises(
        PokeApiError,
        match="invalid UTF-8 response",
    ):
        fetch_localized_pokemon_name(
            "Uxie",
            locale="de_DE",
        )


@patch("novachrono.sources.pokeapi.urlopen")
def test_invalid_json_raises_poke_api_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_raw_response("definitely not json")

    with pytest.raises(
        PokeApiError,
        match="invalid JSON",
    ):
        fetch_localized_pokemon_name(
            "Uxie",
            locale="de_DE",
        )


def _create_roster(
    *,
    five_star_name: str,
    mega_name: str,
) -> RaidRoster:
    return RaidRoster(
        five_star=(
            RaidBoss(
                name=five_star_name,
                can_be_shiny=True,
                artwork_url="https://example.com/mesprit.png",
            ),
        ),
        mega=(
            RaidBoss(
                name=mega_name,
                can_be_shiny=True,
                artwork_url="https://example.com/mega-blaziken.png",
            ),
        ),
    )
