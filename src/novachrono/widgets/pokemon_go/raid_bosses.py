from collections.abc import Mapping
from typing import Final

from PIL import Image, ImageDraw, ImageFont, ImageOps

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_DIM_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    create_panel,
    draw_widget_header,
    find_font_that_fits,
)
from novachrono.pokemon_go import (
    RaidBoss,
    RaidRoster,
    RaidTier,
)

ARTWORK_FRAME_SIZE: Final = 32
ARTWORK_SIZE: Final = 28
ARTWORK_LEFT: Final = 17

TEXT_LEFT: Final = 56
TEXT_RIGHT: Final = 111

FIVE_STAR_SPARKLE_COUNT: Final = 5
FIVE_STAR_SPARKLE_SPACING: Final = 6
FIVE_STAR_SPARKLE_RADIUS: Final = 2

SHINY_COLOR: Final = "#FFD447"


def render_raid_panel(
    roster: RaidRoster,
    *,
    artwork_by_url: Mapping[str, Image.Image] | None = None,
) -> Image.Image:
    """Render the current five-star and Mega raid roster."""

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(
        draw,
        title="POKEMON GO",
        font_size=9,
    )

    _draw_raid_section(
        image,
        draw,
        top=34,
        bottom=66,
        tier=RaidTier.FIVE_STAR,
        bosses=roster.five_star,
        artwork_by_url=artwork_by_url,
    )

    _draw_separator(
        draw,
        y=70,
    )

    _draw_raid_section(
        image,
        draw,
        top=76,
        bottom=108,
        tier=RaidTier.MEGA,
        bosses=roster.mega,
        artwork_by_url=artwork_by_url,
    )

    return image


def render_raid_animation(
    roster: RaidRoster,
    *,
    artwork_by_url: Mapping[str, Image.Image] | None = None,
) -> tuple[Image.Image, ...]:
    """Render all relevant raid bosses as rotating panel frames."""

    frame_count = max(
        1,
        len(roster.five_star),
        len(roster.mega),
    )

    return tuple(
        render_raid_panel(
            _create_frame_roster(
                roster,
                frame_index=frame_index,
            ),
            artwork_by_url=artwork_by_url,
        )
        for frame_index in range(frame_count)
    )


def _create_frame_roster(
    roster: RaidRoster,
    *,
    frame_index: int,
) -> RaidRoster:
    return RaidRoster(
        five_star=_select_boss_for_frame(
            roster.five_star,
            frame_index=frame_index,
        ),
        mega=_select_boss_for_frame(
            roster.mega,
            frame_index=frame_index,
        ),
    )


def _select_boss_for_frame(
    bosses: tuple[RaidBoss, ...],
    *,
    frame_index: int,
) -> tuple[RaidBoss, ...]:
    if not bosses:
        return ()

    return (bosses[frame_index % len(bosses)],)


def _draw_raid_section(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    top: int,
    bottom: int,
    tier: RaidTier,
    bosses: tuple[RaidBoss, ...],
    artwork_by_url: Mapping[str, Image.Image] | None,
) -> None:
    if not bosses:
        _draw_empty_state(
            draw,
            top=top,
            bottom=bottom,
        )
        return

    boss = bosses[0]

    _draw_boss_artwork(
        image,
        draw,
        boss=boss,
        left=ARTWORK_LEFT,
        top=top,
        frame_size=ARTWORK_FRAME_SIZE,
        artwork_size=ARTWORK_SIZE,
        artwork_by_url=artwork_by_url,
    )

    _draw_tier_label(
        draw,
        tier=tier,
        left=TEXT_LEFT,
        top=top,
    )

    _draw_boss_name(
        draw,
        left=TEXT_LEFT,
        right=TEXT_RIGHT,
        artwork_top=top,
        artwork_height=ARTWORK_FRAME_SIZE,
        name=_display_boss_name(
            boss.name,
            tier=tier,
        ),
    )


def _draw_tier_label(
    draw: ImageDraw.ImageDraw,
    *,
    tier: RaidTier,
    left: int,
    top: int,
) -> None:
    if tier is RaidTier.FIVE_STAR:
        _draw_five_star_label(
            draw,
            left=left,
            top=top,
        )
        return

    font = ImageFont.load_default(size=8)

    draw.text(
        (left, top),
        "MEGA",
        font=font,
        fill=FRAME_ACCENT_COLOR,
    )


def _draw_five_star_label(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    top: int,
) -> None:
    center_y = top + 5
    first_center_x = left + FIVE_STAR_SPARKLE_RADIUS

    for index in range(FIVE_STAR_SPARKLE_COUNT):
        center_x = first_center_x + index * FIVE_STAR_SPARKLE_SPACING

        _draw_sparkle(
            draw,
            origin=(center_x, center_y),
            color=FRAME_ACCENT_COLOR,
            radius=FIVE_STAR_SPARKLE_RADIUS,
        )


def _draw_boss_name(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    right: int,
    artwork_top: int,
    artwork_height: int,
    name: str,
) -> None:
    available_width = right - left + 1

    font = find_font_that_fits(
        draw,
        text=name,
        maximum_width=available_width,
        font_sizes=(15, 14, 13, 12, 11, 10, 9),
    )

    bounding_box = draw.textbbox(
        (0, 0),
        name,
        font=font,
    )

    text_height = bounding_box[3] - bounding_box[1]

    y = artwork_top + (artwork_height - text_height) // 2 - bounding_box[1]

    draw.text(
        (left, y),
        name,
        font=font,
        fill=TEXT_COLOR,
    )


def _draw_boss_artwork(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    boss: RaidBoss,
    left: int,
    top: int,
    frame_size: int,
    artwork_size: int,
    artwork_by_url: Mapping[str, Image.Image] | None,
) -> None:
    _draw_artwork_frame(
        draw,
        left=left,
        top=top,
        size=frame_size,
    )

    artwork = _find_artwork(boss, artwork_by_url=artwork_by_url)

    if artwork is None:
        _draw_artwork_placeholder(
            draw,
            left=left,
            top=top,
            size=frame_size,
        )
    else:
        normalized_artwork = artwork.convert("RGBA")

        fitted_artwork = ImageOps.contain(
            normalized_artwork,
            (
                artwork_size,
                artwork_size,
            ),
            method=Image.Resampling.LANCZOS,
        )

        x = left + (frame_size - fitted_artwork.width) // 2
        y = top + (frame_size - fitted_artwork.height) // 2

        image.paste(
            fitted_artwork,
            (x, y),
            fitted_artwork,
        )

    if boss.can_be_shiny:
        _draw_sparkle(
            draw,
            origin=(
                left + frame_size - 4,
                top + frame_size - 4,
            ),
            color=SHINY_COLOR,
            radius=3,
        )


def _find_artwork(
    boss: RaidBoss,
    *,
    artwork_by_url: Mapping[str, Image.Image] | None,
) -> Image.Image | None:
    if boss.artwork_url is None or artwork_by_url is None:
        return None

    return artwork_by_url.get(boss.artwork_url)


def _draw_artwork_frame(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    top: int,
    size: int,
) -> None:
    right = left + size - 1
    bottom = top + size - 1

    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=4,
        outline=FRAME_DIM_COLOR,
        width=1,
    )


def _draw_artwork_placeholder(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    top: int,
    size: int,
) -> None:
    inset = 8
    center_x = left + size // 2
    center_y = top + size // 2

    draw.line(
        (
            left + inset,
            center_y,
            left + size - inset,
            center_y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (
            center_x,
            top + inset,
            center_x,
            top + size - inset,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )


def _draw_sparkle(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    color: str,
    radius: int,
) -> None:
    center_x, center_y = origin

    draw.polygon(
        (
            (center_x, center_y - radius),
            (center_x + 1, center_y - 1),
            (center_x + radius, center_y),
            (center_x + 1, center_y + 1),
            (center_x, center_y + radius),
            (center_x - 1, center_y + 1),
            (center_x - radius, center_y),
            (center_x - 1, center_y - 1),
        ),
        fill=color,
    )


def _draw_empty_state(
    draw: ImageDraw.ImageDraw,
    *,
    top: int,
    bottom: int,
) -> None:
    font = ImageFont.load_default(size=8)
    text = "NO DATA"

    bounding_box = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    text_width = bounding_box[2] - bounding_box[0]

    x = (PANEL_SIZE - text_width) // 2
    y = top + (bottom - top) // 2 - 4

    draw.text(
        (x, y),
        text,
        font=font,
        fill=FRAME_DIM_COLOR,
    )


def _draw_separator(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
) -> None:
    draw.line(
        (
            17,
            y,
            PANEL_SIZE - 17,
            y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (
            47,
            y,
            81,
            y,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )


def _display_boss_name(
    name: str,
    *,
    tier: RaidTier,
) -> str:
    normalized_name = name.strip()

    if tier is RaidTier.MEGA and normalized_name.casefold().startswith(
        (
            "mega ",
            "mega-",
        )
    ):
        normalized_name = normalized_name[5:].strip()

    if "(" in normalized_name:
        normalized_name = normalized_name.split(
            "(",
            maxsplit=1,
        )[0].strip()

    return normalized_name.upper()
