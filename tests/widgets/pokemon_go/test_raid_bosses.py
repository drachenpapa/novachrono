from unittest.mock import patch

from PIL import Image

from novachrono.design import PANEL_SIZE
from novachrono.pokemon_go import (
    CombatPowerRange,
    PokemonType,
    RaidBoss,
    RaidRoster,
    RaidTier,
)
from novachrono.widgets.pokemon_go import (
    render_raid_animation,
    render_raid_panel,
)


def test_render_raid_panel_has_expected_size_and_mode() -> None:
    panel = render_raid_panel(_create_roster())

    assert panel.size == (PANEL_SIZE, PANEL_SIZE)
    assert panel.mode == "RGB"


def test_render_raid_panel_is_deterministic() -> None:
    roster = _create_roster()

    first_panel = render_raid_panel(roster)
    second_panel = render_raid_panel(roster)

    assert first_panel.tobytes() == second_panel.tobytes()


def test_render_raid_panel_supports_empty_roster() -> None:
    panel = render_raid_panel(
        RaidRoster(
            five_star=(),
            mega=(),
        )
    )

    assert panel.size == (PANEL_SIZE, PANEL_SIZE)


def test_render_raid_panel_uses_provided_artwork() -> None:
    artwork_url = "https://example.com/vesprit.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                name="Vesprit",
                tier=RaidTier.FIVE_STAR,
                types=(PokemonType.PSYCHIC,),
                artwork_url=artwork_url,
            ),
        ),
        mega=(),
    )

    artwork = Image.new(
        mode="RGBA",
        size=(4, 4),
        color=(255, 0, 255, 255),
    )

    panel = render_raid_panel(
        roster,
        artwork_by_url={
            artwork_url: artwork,
        },
    )

    assert panel.getpixel((20, 37)) == (255, 0, 255)


def test_render_raid_animation_returns_single_frame_for_single_bosses() -> None:
    roster = _create_roster()

    frames = render_raid_animation(roster)

    assert len(frames) == 1
    assert frames[0].tobytes() == render_raid_panel(roster).tobytes()


def test_render_raid_animation_returns_single_frame_for_empty_roster() -> None:
    frames = render_raid_animation(
        RaidRoster(
            five_star=(),
            mega=(),
        )
    )

    assert len(frames) == 1


def test_render_raid_animation_rotates_all_bosses() -> None:
    five_star = (
        _create_boss(
            name="Five A",
            tier=RaidTier.FIVE_STAR,
            types=(PokemonType.PSYCHIC,),
        ),
        _create_boss(
            name="Five B",
            tier=RaidTier.FIVE_STAR,
            types=(PokemonType.FAIRY,),
        ),
        _create_boss(
            name="Five C",
            tier=RaidTier.FIVE_STAR,
            types=(PokemonType.DRAGON,),
        ),
    )

    mega = (
        _create_boss(
            name="Mega A",
            tier=RaidTier.MEGA,
            types=(PokemonType.FIRE,),
        ),
        _create_boss(
            name="Mega B",
            tier=RaidTier.MEGA,
            types=(PokemonType.WATER,),
        ),
    )

    roster = RaidRoster(
        five_star=five_star,
        mega=mega,
    )

    with patch("novachrono.widgets.pokemon_go.raid_bosses.render_raid_panel") as mocked_render:
        mocked_render.side_effect = (Image.new("RGB", (PANEL_SIZE, PANEL_SIZE)) for _ in range(3))

        frames = render_raid_animation(roster)

    assert len(frames) == 3

    rendered_rosters = [call.args[0] for call in mocked_render.call_args_list]

    assert rendered_rosters == [
        RaidRoster(
            five_star=(five_star[0],),
            mega=(mega[0],),
        ),
        RaidRoster(
            five_star=(five_star[1],),
            mega=(mega[1],),
        ),
        RaidRoster(
            five_star=(five_star[2],),
            mega=(mega[0],),
        ),
    ]


def test_render_raid_animation_preserves_empty_tier() -> None:
    five_star = (
        _create_boss(
            name="Five A",
            tier=RaidTier.FIVE_STAR,
            types=(PokemonType.PSYCHIC,),
        ),
        _create_boss(
            name="Five B",
            tier=RaidTier.FIVE_STAR,
            types=(PokemonType.FAIRY,),
        ),
    )

    roster = RaidRoster(
        five_star=five_star,
        mega=(),
    )

    with patch("novachrono.widgets.pokemon_go.raid_bosses.render_raid_panel") as mocked_render:
        mocked_render.side_effect = (Image.new("RGB", (PANEL_SIZE, PANEL_SIZE)) for _ in range(2))

        render_raid_animation(roster)

    rendered_rosters = [call.args[0] for call in mocked_render.call_args_list]

    assert rendered_rosters == [
        RaidRoster(
            five_star=(five_star[0],),
            mega=(),
        ),
        RaidRoster(
            five_star=(five_star[1],),
            mega=(),
        ),
    ]


def _create_roster() -> RaidRoster:
    return RaidRoster(
        five_star=(
            _create_boss(
                name="Vesprit",
                tier=RaidTier.FIVE_STAR,
                types=(PokemonType.PSYCHIC,),
            ),
        ),
        mega=(
            _create_boss(
                name="Mega-Lohgock",
                tier=RaidTier.MEGA,
                types=(
                    PokemonType.FIRE,
                    PokemonType.FIGHTING,
                ),
            ),
        ),
    )


def _create_boss(
    *,
    name: str,
    tier: RaidTier,
    types: tuple[PokemonType, ...],
    artwork_url: str | None = None,
) -> RaidBoss:
    return RaidBoss(
        name=name,
        tier=tier,
        can_be_shiny=True,
        types=types,
        normal_combat_power=CombatPowerRange(
            minimum=1669,
            maximum=1747,
        ),
        boosted_combat_power=CombatPowerRange(
            minimum=2086,
            maximum=2184,
        ),
        artwork_url=artwork_url,
    )
