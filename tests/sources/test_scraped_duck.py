import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from novachrono.pokemon_go import (
    CombatPowerRange,
    PokemonType,
    RaidBoss,
    RaidTier,
)
from novachrono.sources.scraped_duck import (
    ScrapedDuckError,
    fetch_raid_roster,
)


def create_response(
    payload: object,
) -> MagicMock:
    response = MagicMock()

    response.read.return_value = json.dumps(payload).encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def create_raid(
    *,
    name: str,
    tier: str,
    types: tuple[str, ...],
    shiny: bool = True,
    image_url: str = "https://example.com/artwork.png",
) -> dict[str, object]:
    return {
        "name": name,
        "tier": tier,
        "canBeShiny": shiny,
        "types": [
            {
                "name": pokemon_type,
                "image": "ignored",
            }
            for pokemon_type in types
        ],
        "combatPower": {
            "normal": {
                "min": 2100,
                "max": 2188,
            },
            "boosted": {
                "min": 2625,
                "max": 2735,
            },
        },
        "boostedWeather": [],
        "image": image_url,
    }


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_normalizes_relevant_raids(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = create_response(
        [
            create_raid(
                name="Zacian (Crowned Sword)",
                tier="5-Star Raids",
                types=(
                    "fairy",
                    "steel",
                ),
                image_url="https://example.com/zacian.png",
            ),
            create_raid(
                name="Mega Gengar",
                tier="Mega Raids",
                types=(
                    "ghost",
                    "poison",
                ),
                image_url="https://example.com/mega-gengar.png",
            ),
            create_raid(
                name="Shadow Ralts",
                tier="1-Star Raids",
                types=(
                    "psychic",
                    "fairy",
                ),
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert roster.five_star == (
        RaidBoss(
            name="Zacian (Crowned Sword)",
            tier=RaidTier.FIVE_STAR,
            can_be_shiny=True,
            types=(
                PokemonType.FAIRY,
                PokemonType.STEEL,
            ),
            normal_combat_power=CombatPowerRange(
                minimum=2100,
                maximum=2188,
            ),
            boosted_combat_power=CombatPowerRange(
                minimum=2625,
                maximum=2735,
            ),
            artwork_url="https://example.com/zacian.png",
        ),
    )

    assert len(roster.mega) == 1
    assert roster.mega[0].name == "Mega Gengar"
    assert roster.mega[0].artwork_url == "https://example.com/mega-gengar.png"


@patch("novachrono.sources.scraped_duck.urlopen")
def test_fetch_raid_roster_ignores_shadow_five_star_raids(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = create_response(
        [
            create_raid(
                name="Uxie",
                tier="5-Star Raids",
                types=("psychic",),
            ),
            create_raid(
                name="Mesprit",
                tier="5-Star Raids",
                types=("psychic",),
            ),
            create_raid(
                name="Azelf",
                tier="5-Star Raids",
                types=("psychic",),
            ),
            create_raid(
                name="Shadow Giratina",
                tier="5-Star Raids",
                types=(
                    "ghost",
                    "dragon",
                ),
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
    mocked_urlopen.return_value = create_response(
        [
            create_raid(
                name="Zacian",
                tier="5-Star Raids",
                types=("fairy",),
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
    mocked_urlopen.return_value = create_response(
        [
            create_raid(
                name="Zacian",
                tier="5-Star Raids",
                types=("fairy",),
            ),
            create_raid(
                name="Zamazenta",
                tier="5-Star Raids",
                types=("fighting",),
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
    mocked_urlopen.return_value = create_response(
        [
            create_raid(
                name="Five Star",
                tier="Tier 5",
                types=("dragon",),
            ),
            create_raid(
                name="Mega Boss",
                tier="Mega",
                types=("fire",),
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
    mocked_urlopen.return_value = create_response(
        [
            create_raid(
                name="Tier One",
                tier="1-Star Raids",
                types=("normal",),
            ),
            create_raid(
                name="Tier Three",
                tier="3-Star Raids",
                types=("rock",),
            ),
        ]
    )

    roster = fetch_raid_roster()

    assert roster.five_star == ()
    assert roster.mega == ()


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
def test_fetch_raid_roster_rejects_invalid_json(
    mocked_urlopen: MagicMock,
) -> None:
    response = MagicMock()
    response.read.return_value = b"not-json"

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    mocked_urlopen.return_value = context_manager

    with pytest.raises(
        ScrapedDuckError,
        match="invalid JSON",
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
