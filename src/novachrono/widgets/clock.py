from datetime import datetime
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_BRIGHT_COLOR,
    FRAME_DEEP_COLOR,
    FRAME_DIM_COLOR,
    MUTED_TEXT_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    create_panel,
    draw_centered_text,
    draw_widget_header,
)

CLOCK_TITLE: Final = "NOVACHRONO"

CLOCK_FRAME_COUNT: Final = 26

TIME_TOP: Final = 39
HORIZON_Y: Final = 76
DATE_TOP: Final = 88
BOTTOM_ACCENT_Y: Final = 104

HORIZON_LEFT: Final = 17
HORIZON_RIGHT: Final = PANEL_SIZE - 17

TRACER_LENGTH: Final = 7


def render_clock_panel(now: datetime) -> Image.Image:
    """Render the first frame of the Novachrono clock animation."""

    _validate_datetime(now)

    return _render_clock_frame(now, tracer_progress=0.0)


def render_clock_animation(now: datetime) -> tuple[Image.Image, ...]:
    """Render the Novachrono clock animation."""

    _validate_datetime(now)

    return tuple(
        _render_clock_frame(now, tracer_progress=_sweep_progress(frame_index))
        for frame_index in range(CLOCK_FRAME_COUNT)
    )


def _validate_datetime(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Clock widget requires a timezone-aware datetime")


def _render_clock_frame(
    now: datetime,
    *,
    tracer_progress: float,
) -> Image.Image:
    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(
        draw,
        title=CLOCK_TITLE,
        font_size=11,
    )

    draw_centered_text(
        draw,
        y=TIME_TOP,
        text=now.strftime("%H:%M"),
        font=ImageFont.load_default(size=32),
        fill=TEXT_COLOR,
    )

    _draw_horizon(draw)

    _draw_tracer(draw, progress=tracer_progress)

    draw_centered_text(
        draw,
        y=DATE_TOP,
        text=now.strftime("%d.%m.%Y"),
        font=ImageFont.load_default(size=10),
        fill=MUTED_TEXT_COLOR,
    )

    _draw_bottom_accent(draw)

    return image


def _draw_horizon(draw: ImageDraw.ImageDraw) -> None:
    """Draw the inactive Horizon line."""

    draw.line(
        (
            HORIZON_LEFT,
            HORIZON_Y,
            56,
            HORIZON_Y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (
            56,
            HORIZON_Y,
            60,
            HORIZON_Y - 4,
            64,
            HORIZON_Y,
            68,
            HORIZON_Y + 4,
            72,
            HORIZON_Y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (
            72,
            HORIZON_Y,
            HORIZON_RIGHT,
            HORIZON_Y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    for x, height in (
        (24, 3),
        (32, 5),
        (40, 2),
        (88, 2),
        (96, 5),
        (104, 3),
    ):
        draw.line(
            (
                x,
                HORIZON_Y,
                x,
                HORIZON_Y + height,
            ),
            fill=FRAME_DEEP_COLOR,
            width=1,
        )


def _draw_bottom_accent(draw: ImageDraw.ImageDraw) -> None:
    draw.line(
        (
            46,
            BOTTOM_ACCENT_Y,
            82,
            BOTTOM_ACCENT_Y,
        ),
        fill=FRAME_DEEP_COLOR,
        width=1,
    )


def _draw_tracer(
    draw: ImageDraw.ImageDraw,
    *,
    progress: float,
) -> None:
    path = _horizon_path()

    maximum_start = max(0, len(path) - TRACER_LENGTH)

    start = round(maximum_start * progress)

    tracer_points = path[start : start + TRACER_LENGTH]

    if len(tracer_points) >= 2:
        draw.line(
            tracer_points,
            fill=FRAME_ACCENT_COLOR,
            width=2,
        )

    if tracer_points:
        draw.point(
            tracer_points[-1],
            fill=FRAME_BRIGHT_COLOR,
        )


def _sweep_progress(frame_index: int) -> float:
    """Move the tracer from left to right and back."""

    half_cycle = (CLOCK_FRAME_COUNT - 1) / 2
    distance_from_center = abs(frame_index - half_cycle)

    return 1.0 - distance_from_center / half_cycle


def _horizon_path() -> tuple[tuple[int, int], ...]:
    """Return the complete Horizon path from left to right."""

    points: list[tuple[int, int]] = []

    for x in range(HORIZON_LEFT, 57):
        points.append((x, HORIZON_Y))

    points.extend(
        (
            (57, 75),
            (58, 74),
            (59, 73),
            (60, 72),
            (61, 73),
            (62, 74),
            (63, 75),
            (64, 76),
            (65, 77),
            (66, 78),
            (67, 79),
            (68, 80),
            (69, 79),
            (70, 78),
            (71, 77),
            (72, 76),
        )
    )

    for x in range(
        73,
        HORIZON_RIGHT + 1,
    ):
        points.append((x, HORIZON_Y))

    return tuple(points)
