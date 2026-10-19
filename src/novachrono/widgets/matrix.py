from typing import Final

from PIL import Image, ImageDraw, ImageFont

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_DIM_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    create_panel,
)

MATRIX_FRAME_DURATION_MS: Final = 200

_FRAME_COUNT: Final = 10

_CONTENT_LEFT: Final = 14
_CONTENT_RIGHT: Final = PANEL_SIZE - 14
_CONTENT_TOP: Final = 16
_CONTENT_BOTTOM: Final = PANEL_SIZE - 14

_COLUMN_SPACING: Final = 10
_GLYPH_HEIGHT: Final = 9

_GLYPHS: Final = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F")
_COLUMN_OFFSETS: Final = (2, 8, 4, 11, 0, 6, 13, 3, 9, 5)
_COLUMN_SPEEDS: Final = (1, 2, 1, 3, 2, 1, 2, 3, 1, 2)
_COLUMN_LENGTHS: Final = (5, 7, 4, 6, 5, 7, 4, 6, 5, 7)


def render_matrix_panel() -> Image.Image:
    """Render the first Matrix-style animation frame."""

    return _render_matrix_frame(frame_index=0)


def render_matrix_animation() -> tuple[Image.Image, ...]:
    """Render the complete Matrix-style animation."""

    return tuple(
        _render_matrix_frame(frame_index=frame_index) for frame_index in range(_FRAME_COUNT)
    )


def _render_matrix_frame(
    *,
    frame_index: int,
) -> Image.Image:
    image = create_panel()
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=8)
    column_count = (_CONTENT_RIGHT - _CONTENT_LEFT) // _COLUMN_SPACING

    for column_index in range(column_count):
        x = _CONTENT_LEFT + column_index * _COLUMN_SPACING
        offset = _COLUMN_OFFSETS[column_index % len(_COLUMN_OFFSETS)]
        speed = _COLUMN_SPEEDS[column_index % len(_COLUMN_SPEEDS)]
        trail_length = _COLUMN_LENGTHS[column_index % len(_COLUMN_LENGTHS)]
        head_row = (offset + frame_index * speed) % _row_count()

        _draw_column(
            draw,
            font=font,
            column_index=column_index,
            x=x,
            head_row=head_row,
            trail_length=trail_length,
            frame_index=frame_index,
        )

    return image


def _draw_column(
    draw: ImageDraw.ImageDraw,
    *,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    column_index: int,
    x: int,
    head_row: int,
    trail_length: int,
    frame_index: int,
) -> None:
    for trail_index in range(trail_length):
        row = head_row - trail_index

        if row < 0:
            row += _row_count()

        y = _CONTENT_TOP + row * _GLYPH_HEIGHT

        if y > _CONTENT_BOTTOM:
            continue

        glyph = _glyph_for_position(column_index=column_index, row=row, frame_index=frame_index)
        draw.text((x, y), glyph, font=font, fill=_trail_color(trail_index))


def _glyph_for_position(
    *,
    column_index: int,
    row: int,
    frame_index: int,
) -> str:
    glyph_index = (column_index * 5 + row * 3 + frame_index) % len(_GLYPHS)

    return _GLYPHS[glyph_index]


def _trail_color(trail_index: int) -> str:
    if trail_index == 0:
        return TEXT_COLOR

    if trail_index <= 2:
        return FRAME_ACCENT_COLOR

    return FRAME_DIM_COLOR


def _row_count() -> int:
    return (_CONTENT_BOTTOM - _CONTENT_TOP) // _GLYPH_HEIGHT + 1
