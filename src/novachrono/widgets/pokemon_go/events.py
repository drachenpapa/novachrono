from collections.abc import Mapping
from datetime import datetime
from typing import Final

from PIL import Image, ImageDraw, ImageFont, ImageOps

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_DIM_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    create_panel,
    draw_centered_text,
    draw_widget_header,
    find_font_that_fits,
)
from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoEventType,
    PokemonGoFeaturedPokemon,
)
from novachrono.widgets.pokemon_go._drawing import (
    SHINY_COLOR,
    draw_sparkle,
)

EVENT_FRAME_DURATION_MS: Final = 30_000

ARTWORK_SIZE: Final = 38
ARTWORK_TOP: Final = 35
ARTWORK_LEFT: Final = (PANEL_SIZE - ARTWORK_SIZE) // 2

NAME_TOP: Final = 76
NAME_BOTTOM: Final = 88

TIME_TOP: Final = 90
TIME_BOTTOM: Final = 99

BONUS_TOP: Final = 101
BONUS_BOTTOM: Final = 109

CONTENT_LEFT: Final = 17
CONTENT_RIGHT: Final = PANEL_SIZE - 17

_EVENT_TITLES: Final = {
    PokemonGoEventType.COMMUNITY_DAY: "COMMUNITY DAY",
    PokemonGoEventType.COMMUNITY_DAY_CLASSIC: "CD CLASSIC",
    PokemonGoEventType.SPOTLIGHT_HOUR: "SPOTLIGHT HOUR",
    PokemonGoEventType.MAX_MONDAY: "MAX MONDAY",
}

_DATE_FORMATS: Final = {
    "de_DE": "%d.%m.",
    "en_US": "%m/%d",
}


def render_event_panel(
    schedule: EventSchedule,
    *,
    locale: str,
    artwork_by_url: Mapping[str, Image.Image] | None = None,
) -> Image.Image:
    """Render the first available Pokémon GO event frame."""

    frames = _event_frames(schedule)

    if not frames:
        return _render_empty_panel()

    event, pokemon = frames[0]

    return _render_event(event, pokemon=pokemon, locale=locale, artwork_by_url=artwork_by_url)


def render_event_animation(
    schedule: EventSchedule,
    *,
    locale: str,
    artwork_by_url: Mapping[str, Image.Image] | None = None,
) -> tuple[Image.Image, ...]:
    """Render one frame per featured Pokémon."""

    frames = _event_frames(schedule)

    if not frames:
        return (_render_empty_panel(),)

    return tuple(
        _render_event(event, pokemon=pokemon, locale=locale, artwork_by_url=artwork_by_url)
        for event, pokemon in frames
    )


def _event_frames(
    schedule: EventSchedule,
) -> tuple[tuple[PokemonGoEvent, PokemonGoFeaturedPokemon | None], ...]:
    frames: list[tuple[PokemonGoEvent, PokemonGoFeaturedPokemon | None]] = []

    for event in _scheduled_events(schedule):
        if not event.featured_pokemon:
            frames.append((event, None))
            continue

        frames.extend((event, pokemon) for pokemon in event.featured_pokemon)

    return tuple(frames)


def _scheduled_events(schedule: EventSchedule) -> tuple[PokemonGoEvent, ...]:
    return tuple(
        event
        for event in (
            schedule.community_day,
            schedule.community_day_classic,
            schedule.spotlight_hour,
            schedule.max_monday,
        )
        if event is not None
    )


def _render_event(
    event: PokemonGoEvent,
    *,
    pokemon: PokemonGoFeaturedPokemon | None,
    locale: str,
    artwork_by_url: Mapping[str, Image.Image] | None,
) -> Image.Image:
    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(draw, title=_EVENT_TITLES[event.event_type], font_size=9)

    _draw_event_artwork(image, draw, pokemon=pokemon, artwork_by_url=artwork_by_url)

    if pokemon is not None:
        _draw_centered_fitted_text(
            draw,
            text=pokemon.name.upper(),
            top=NAME_TOP,
            bottom=NAME_BOTTOM,
            font_sizes=(14, 13, 12, 11, 10, 9),
            fill=TEXT_COLOR,
        )

    _draw_centered_fitted_text(
        draw,
        text=_format_event_time(event, locale=locale),
        top=TIME_TOP,
        bottom=TIME_BOTTOM,
        font_sizes=(10, 9, 8),
        fill=FRAME_ACCENT_COLOR,
    )

    if event.bonus is not None:
        _draw_centered_fitted_text(
            draw,
            text=_format_bonus(event.bonus),
            top=BONUS_TOP,
            bottom=BONUS_BOTTOM,
            font_sizes=(9, 8, 7),
            fill=TEXT_COLOR,
        )

    return image


def _render_empty_panel() -> Image.Image:
    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(draw, title="EVENTS", font_size=9)

    font = ImageFont.load_default(size=9)
    bounding_box = draw.textbbox((0, 0), "NO EVENTS", font=font)

    text_height = bounding_box[3] - bounding_box[1]
    y = 71 - text_height // 2 - bounding_box[1]

    draw_centered_text(draw, y=y, text="NO EVENTS", font=font, fill=FRAME_DIM_COLOR)

    return image


def _draw_event_artwork(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    pokemon: PokemonGoFeaturedPokemon | None,
    artwork_by_url: Mapping[str, Image.Image] | None,
) -> None:
    artwork = _find_artwork(pokemon, artwork_by_url=artwork_by_url)

    if artwork is None:
        _draw_artwork_placeholder(draw)
    else:
        fitted_artwork = ImageOps.contain(
            artwork.convert("RGBA"), (ARTWORK_SIZE, ARTWORK_SIZE), method=Image.Resampling.LANCZOS
        )

        x = (PANEL_SIZE - fitted_artwork.width) // 2
        y = ARTWORK_TOP + (ARTWORK_SIZE - fitted_artwork.height) // 2

        image.paste(fitted_artwork, (x, y), fitted_artwork)

    if pokemon is not None and pokemon.can_be_shiny is True:
        draw_sparkle(
            draw,
            origin=(ARTWORK_LEFT + ARTWORK_SIZE - 3, ARTWORK_TOP + ARTWORK_SIZE - 3),
            color=SHINY_COLOR,
            radius=3,
        )


def _find_artwork(
    pokemon: PokemonGoFeaturedPokemon | None,
    *,
    artwork_by_url: Mapping[str, Image.Image] | None,
) -> Image.Image | None:
    if pokemon is None or pokemon.artwork_url is None or artwork_by_url is None:
        return None

    return artwork_by_url.get(pokemon.artwork_url)


def _draw_artwork_placeholder(draw: ImageDraw.ImageDraw) -> None:
    inset = 10

    center_x = PANEL_SIZE // 2
    center_y = ARTWORK_TOP + ARTWORK_SIZE // 2

    draw.line(
        (ARTWORK_LEFT + inset, center_y, ARTWORK_LEFT + ARTWORK_SIZE - inset, center_y),
        fill=FRAME_DIM_COLOR,
        width=1,
    )
    draw.line(
        (center_x, ARTWORK_TOP + inset, center_x, ARTWORK_TOP + ARTWORK_SIZE - inset),
        fill=FRAME_DIM_COLOR,
        width=1,
    )


def _draw_centered_fitted_text(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    top: int,
    bottom: int,
    font_sizes: tuple[int, ...],
    fill: str,
) -> None:
    available_width = CONTENT_RIGHT - CONTENT_LEFT + 1
    font = find_font_that_fits(
        draw, text=text, maximum_width=available_width, font_sizes=font_sizes
    )

    bounding_box = draw.textbbox((0, 0), text, font=font)

    text_height = bounding_box[3] - bounding_box[1]
    y = top + (bottom - top + 1 - text_height) // 2 - bounding_box[1]

    draw_centered_text(draw, y=y, text=text, font=font, fill=fill)


def _format_bonus(bonus: str) -> str:
    return bonus.replace(
        "\u00d7",
        "x",
    ).upper()


def _format_event_time(
    event: PokemonGoEvent,
    *,
    locale: str,
) -> str:
    date_format = _DATE_FORMATS.get(locale, _DATE_FORMATS["en_US"])

    date_text = event.start.strftime(date_format)

    if event.event_type is PokemonGoEventType.MAX_MONDAY:
        return date_text

    return f"{date_text} {_format_clock_time(event.start)}-{_format_clock_time(event.end)}h"


def _format_clock_time(value: datetime) -> str:
    if value.minute == 0:
        return str(value.hour)

    return f"{value.hour}:{value.minute:02d}"
