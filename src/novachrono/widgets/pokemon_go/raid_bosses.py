from collections.abc import Mapping
from typing import Final

from PIL import Image, ImageDraw

from novachrono.design import (
    create_panel,
    draw_widget_header,
)
from novachrono.models.pokemon_go import (
    RaidBoss,
    RaidRoster,
    RaidTier,
)
from novachrono.widgets.pokemon_go._raid_layout import (
    _draw_dual_raid_layout,
    _draw_empty_state,
    _draw_single_raid_layout,
)

RAID_FRAME_DURATION_MS: Final = 10_000


def render_raid_panel(
    roster: RaidRoster,
    *,
    artwork_by_url: Mapping[str, Image.Image] | None = None,
) -> Image.Image:
    """Render the current five-star, Shadow five-star, and Mega raid roster."""

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(draw, title="POKEMON GO", font_size=11)

    upper_raid = _first_upper_raid(roster)

    if upper_raid is not None and roster.mega:
        upper_tier, upper_boss = upper_raid

        _draw_dual_raid_layout(
            image,
            draw,
            upper_tier=upper_tier,
            upper_boss=upper_boss,
            mega_boss=roster.mega[0],
            artwork_by_url=artwork_by_url,
        )
    elif upper_raid is not None:
        upper_tier, upper_boss = upper_raid

        _draw_single_raid_layout(
            image,
            draw,
            tier=upper_tier,
            boss=upper_boss,
            artwork_by_url=artwork_by_url,
        )
    elif roster.mega:
        _draw_single_raid_layout(
            image,
            draw,
            tier=RaidTier.MEGA,
            boss=roster.mega[0],
            artwork_by_url=artwork_by_url,
        )
    else:
        _draw_empty_state(draw, top=34, bottom=108)

    return image


def render_raid_animation(
    roster: RaidRoster,
    *,
    artwork_by_url: Mapping[str, Image.Image] | None = None,
) -> tuple[Image.Image, ...]:
    """Render all relevant raid bosses as rotating panel frames."""

    frame_count = max(1, len(_upper_raids(roster)), len(roster.mega))

    return tuple(
        render_raid_panel(
            _create_frame_roster(roster, frame_index=frame_index), artwork_by_url=artwork_by_url
        )
        for frame_index in range(frame_count)
    )


def _create_frame_roster(
    roster: RaidRoster,
    *,
    frame_index: int,
) -> RaidRoster:
    selected_upper_raid = _select_upper_raid_for_frame(
        _upper_raids(roster), frame_index=frame_index
    )
    selected_mega_boss = _select_boss_for_frame(roster.mega, frame_index=frame_index)

    five_star: tuple[RaidBoss, ...] = ()
    shadow_five_star: tuple[RaidBoss, ...] = ()

    mega: tuple[RaidBoss, ...] = (selected_mega_boss,) if selected_mega_boss is not None else ()

    if selected_upper_raid is not None:
        tier, boss = selected_upper_raid

        if tier is RaidTier.FIVE_STAR:
            five_star = (boss,)
        elif tier is RaidTier.SHADOW_FIVE_STAR:
            shadow_five_star = (boss,)

    return RaidRoster(five_star=five_star, mega=mega, shadow_five_star=shadow_five_star)


def _upper_raids(roster: RaidRoster) -> tuple[tuple[RaidTier, RaidBoss], ...]:
    five_star = tuple((RaidTier.FIVE_STAR, boss) for boss in roster.five_star)

    shadow_five_star = tuple((RaidTier.SHADOW_FIVE_STAR, boss) for boss in roster.shadow_five_star)

    return five_star + shadow_five_star


def _select_upper_raid_for_frame(
    raids: tuple[tuple[RaidTier, RaidBoss], ...],
    *,
    frame_index: int,
) -> tuple[RaidTier, RaidBoss] | None:
    if not raids:
        return None

    return raids[frame_index % len(raids)]


def _select_boss_for_frame(
    bosses: tuple[RaidBoss, ...],
    *,
    frame_index: int,
) -> RaidBoss | None:
    if not bosses:
        return None

    return bosses[frame_index % len(bosses)]


def _first_upper_raid(roster: RaidRoster) -> tuple[RaidTier, RaidBoss] | None:
    if roster.five_star:
        return (RaidTier.FIVE_STAR, roster.five_star[0])

    if roster.shadow_five_star:
        return (RaidTier.SHADOW_FIVE_STAR, roster.shadow_five_star[0])

    return None
