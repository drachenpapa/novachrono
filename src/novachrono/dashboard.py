from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

from novachrono.config import DEFAULT_TIMEZONE_NAME
from novachrono.i18n import DEFAULT_LOCALE
from novachrono.models.pokemon_go import EventSchedule, RaidRoster
from novachrono.models.weather import CurrentWeather
from novachrono.units import TemperatureUnit
from novachrono.widgets.clock import render_clock_panel
from novachrono.widgets.matrix import render_matrix_panel
from novachrono.widgets.pokemon_go import render_event_panel, render_raid_panel
from novachrono.widgets.weather import render_weather_panel

DEFAULT_TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE_NAME)

MATRIX_PANEL_INDEX = 0
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

    return (
        render_matrix_panel(),
        render_weather_panel(weather, locale=locale, temperature_unit=temperature_unit),
        render_clock_panel(current_time, locale=locale),
        render_raid_panel(raid_roster, artwork_by_url=raid_artwork),
        render_event_panel(event_schedule, locale=locale, artwork_by_url=event_artwork),
    )
