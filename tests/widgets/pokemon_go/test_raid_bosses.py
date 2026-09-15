from unittest.mock import patch

from PIL import Image

from novachrono.design import PANEL_SIZE
from novachrono.pokemon_go import RaidBoss, RaidRoster
from novachrono.widgets.pokemon_go import (
    render_raid_animation,
    render_raid_panel,
)


def test_render_raid_panel_has_expected_size_and_mode() -> None:
    panel = render_raid_panel(_create_roster())

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
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

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )


def test_render_raid_panel_uses_provided_artwork() -> None:
    artwork_url = "https://example.com/vesprit.png"

    roster = RaidRoster(
        five_star=(
            _create_boss(
                name="Vesprit",
                artwork_url=artwork_url,
            ),
        ),
        mega=(),
    )

    artwork = Image.new(
        mode="RGB",
        size=(44, 44),
        color=(255, 0, 255),
    )

    panel_with_artwork = render_raid_panel(
        roster,
        artwork_by_url={
            artwork_url: artwork,
        },
    )

    panel_without_artwork = render_raid_panel(roster)

    assert panel_with_artwork.tobytes() != panel_without_artwork.tobytes()
    assert (255, 0, 255) in set(panel_with_artwork.get_flattened_data())


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
        ),
        _create_boss(
            name="Five B",
        ),
        _create_boss(
            name="Five C",
        ),
    )

    mega = (
        _create_boss(
            name="Mega A",
        ),
        _create_boss(
            name="Mega B",
        ),
    )

    roster = RaidRoster(
        five_star=five_star,
        mega=mega,
    )

    with patch("novachrono.widgets.pokemon_go.raid_bosses.render_raid_panel") as mocked_render:
        mocked_render.side_effect = (
            Image.new(
                "RGB",
                (
                    PANEL_SIZE,
                    PANEL_SIZE,
                ),
            )
            for _ in range(3)
        )

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
        ),
        _create_boss(
            name="Five B",
        ),
    )

    roster = RaidRoster(
        five_star=five_star,
        mega=(),
    )

    with patch("novachrono.widgets.pokemon_go.raid_bosses.render_raid_panel") as mocked_render:
        mocked_render.side_effect = (
            Image.new(
                "RGB",
                (
                    PANEL_SIZE,
                    PANEL_SIZE,
                ),
            )
            for _ in range(2)
        )

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
            ),
        ),
        mega=(
            _create_boss(
                name="Mega-Lohgock",
            ),
        ),
    )


def _create_boss(
    *,
    name: str,
    artwork_url: str | None = None,
) -> RaidBoss:
    return RaidBoss(
        name=name,
        can_be_shiny=True,
        artwork_url=artwork_url,
    )
