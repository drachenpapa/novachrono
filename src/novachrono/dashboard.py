from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from novachrono.config import DEFAULT_TIMEZONE_NAME
from novachrono.design import (
    FRAME_ACCENT_COLOR,
    PANEL_COUNT,
    create_panel,
    draw_placeholder_header,
)
from novachrono.i18n import DEFAULT_LOCALE
from novachrono.models.pokemon_go import EventSchedule, RaidRoster
from novachrono.models.weather import CurrentWeather
from novachrono.units import TemperatureUnit
from novachrono.widgets.clock import render_clock_panel
from novachrono.widgets.pokemon_go import render_event_panel, render_raid_panel
from novachrono.widgets.weather import render_weather_panel

DEFAULT_TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE_NAME)

WEATHER_PANEL_INDEX = 1
CLOCK_PANEL_INDEX = 2
RAID_PANEL_INDEX = 3
EVENT_PANEL_INDEX = 4


def render_dashboard(
    now: datetime | None = None,
    *,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
    event_artwork: Mapping[str, Image.Image] | None = None,
    raid_artwork: Mapping[str, Image.Image] | None = None,
    timezone: ZoneInfo = DEFAULT_TIMEZONE,
    locale: str = DEFAULT_LOCALE,
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
) -> tuple[Image.Image, ...]:
    """Render all Times Gate panels."""

    current_time = now if now is not None else datetime.now(timezone)

    panels = [_render_placeholder_panel() for _ in range(PANEL_COUNT)]

    panels[EVENT_PANEL_INDEX] = render_event_panel(
        event_schedule, locale=locale, artwork_by_url=event_artwork
    )
    panels[WEATHER_PANEL_INDEX] = render_weather_panel(
        weather, locale=locale, temperature_unit=temperature_unit
    )
    panels[CLOCK_PANEL_INDEX] = render_clock_panel(current_time, locale=locale)
    panels[RAID_PANEL_INDEX] = render_raid_panel(raid_roster, artwork_by_url=raid_artwork)

    return tuple(panels)


def _render_placeholder_panel() -> Image.Image:
    """Render one static placeholder panel."""

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_placeholder_header(draw, accent_color=FRAME_ACCENT_COLOR)

    return image
