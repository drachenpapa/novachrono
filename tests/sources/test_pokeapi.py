import json
from unittest.mock import MagicMock, patch

from novachrono.pokemon_go import (
    CombatPowerRange,
    PokemonType,
    RaidBoss,
    RaidRoster,
    RaidTier,
)
from novachrono.sources.pokeapi import (
    fetch_localized_pokemon_name,
    localize_raid_roster,
)


def create_response(localized_name: str) -> MagicMock:
    response = MagicMock()

    response.read.return_value = json.dumps(
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
    ).encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


@patch("novachrono.sources.pokeapi.urlopen")
def test_fetch_localized_pokemon_name_returns_german_name(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = create_response("Selfe")

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
    mocked_urlopen.return_value = create_response("Lohgock")

    name = fetch_localized_pokemon_name(
        "Mega Blaziken",
        locale="de_DE",
    )

    assert name == "Mega-Lohgock"

    request = mocked_urlopen.call_args.args[0]

    assert "/pokemon-species/blaziken/" in request.full_url


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

    assert localized.five_star[0].name == "Mesprit"
    assert localized.five_star[0].artwork_url == "https://example.com/mesprit.png"

    assert localized.mega[0].name == "Mega Blaziken"
    assert localized.mega[0].artwork_url == "https://example.com/mega-blaziken.png"


def _create_roster(
    *,
    five_star_name: str,
    mega_name: str,
) -> RaidRoster:
    return RaidRoster(
        five_star=(
            RaidBoss(
                name=five_star_name,
                tier=RaidTier.FIVE_STAR,
                can_be_shiny=True,
                types=(PokemonType.PSYCHIC,),
                normal_combat_power=CombatPowerRange(
                    minimum=1669,
                    maximum=1747,
                ),
                boosted_combat_power=CombatPowerRange(
                    minimum=2086,
                    maximum=2184,
                ),
                artwork_url="https://example.com/mesprit.png",
            ),
        ),
        mega=(
            RaidBoss(
                name=mega_name,
                tier=RaidTier.MEGA,
                can_be_shiny=True,
                types=(
                    PokemonType.FIRE,
                    PokemonType.FIGHTING,
                ),
                normal_combat_power=CombatPowerRange(
                    minimum=1788,
                    maximum=1867,
                ),
                boosted_combat_power=CombatPowerRange(
                    minimum=2235,
                    maximum=2334,
                ),
                artwork_url="https://example.com/mega-blaziken.png",
            ),
        ),
    )
