from datetime import datetime

import typer

from novachrono.cli._common import (
    ForceOption,
    HostOption,
    TokenOption,
    _cached_fingerprint_matches,
    _create_times_gate_client,
    _load_app_config,
    _load_current_weather,
    _load_event_schedule,
    _load_raw_raid_roster,
    _send_widget_frames,
    _write_fingerprint_or_warn,
)
from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    EVENT_PANEL_INDEX,
    RAID_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
)
from novachrono.display_state import (
    EVENT_STATE_PATH,
    RAID_STATE_PATH,
    WEATHER_STATE_PATH,
    event_schedule_fingerprint,
    raid_roster_fingerprint,
    weather_fingerprint,
)
from novachrono.sources.pokeapi import (
    localize_raid_roster,
)
from novachrono.sources.pokemon_artwork import (
    fetch_event_artwork,
    fetch_raid_artwork,
)
from novachrono.widgets.clock import render_clock_panel
from novachrono.widgets.pokemon_go import (
    EVENT_FRAME_DURATION_MS,
    RAID_FRAME_DURATION_MS,
    render_event_animation,
    render_raid_animation,
)
from novachrono.widgets.weather import (
    render_weather_animation,
    weather_frame_duration_ms,
)


def send_events(
    host: HostOption = None,
    token: TokenOption = None,
    force: ForceOption = False,
) -> None:
    """Retrieve and send Pokémon GO events when the schedule has changed."""

    app_config = _load_app_config()
    client = _create_times_gate_client(app_config=app_config, host=host, local_token=token)

    event_schedule = _load_event_schedule(app_config)

    fingerprint = event_schedule_fingerprint(event_schedule, locale=app_config.locale)

    if not force and _cached_fingerprint_matches(EVENT_STATE_PATH, fingerprint):
        typer.echo("Pokémon GO events unchanged; display update skipped.")
        return

    event_artwork = fetch_event_artwork(event_schedule)

    frames = render_event_animation(
        event_schedule, locale=app_config.locale, artwork_by_url=event_artwork
    )

    _send_widget_frames(
        client=client,
        panel_index=EVENT_PANEL_INDEX,
        frames=frames,
        frame_duration_ms=(EVENT_FRAME_DURATION_MS if len(frames) > 1 else None),
        name="Pokémon GO events",
    )

    _write_fingerprint_or_warn(EVENT_STATE_PATH, fingerprint)


def send_weather(
    host: HostOption = None,
    token: TokenOption = None,
    force: ForceOption = False,
) -> None:
    """Retrieve and send weather when the displayed state has changed."""

    app_config = _load_app_config()
    client = _create_times_gate_client(app_config=app_config, host=host, local_token=token)

    weather = _load_current_weather(app_config)

    fingerprint = weather_fingerprint(
        weather,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    if not force and _cached_fingerprint_matches(WEATHER_STATE_PATH, fingerprint):
        typer.echo("Weather unchanged; display update skipped.")
        return

    frames = render_weather_animation(
        weather,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    _send_widget_frames(
        client=client,
        panel_index=WEATHER_PANEL_INDEX,
        frames=frames,
        frame_duration_ms=weather_frame_duration_ms(weather.condition),
        name="Weather",
    )

    _write_fingerprint_or_warn(WEATHER_STATE_PATH, fingerprint)


def send_clock(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Render and send the clock panel."""

    app_config = _load_app_config()
    client = _create_times_gate_client(app_config=app_config, host=host, local_token=token)

    panel = render_clock_panel(datetime.now(app_config.timezone), locale=app_config.locale)

    _send_widget_frames(
        client=client,
        panel_index=CLOCK_PANEL_INDEX,
        frames=(panel,),
        frame_duration_ms=None,
        name="Clock",
    )


def send_raids(
    host: HostOption = None,
    token: TokenOption = None,
    force: ForceOption = False,
) -> None:
    """Retrieve and send Pokémon GO raids when the roster has changed."""

    app_config = _load_app_config()
    client = _create_times_gate_client(app_config=app_config, host=host, local_token=token)

    raw_raid_roster = _load_raw_raid_roster()
    raid_roster = localize_raid_roster(raw_raid_roster, locale=app_config.locale)
    fingerprint = raid_roster_fingerprint(raid_roster, locale=app_config.locale)

    if not force and _cached_fingerprint_matches(RAID_STATE_PATH, fingerprint):
        typer.echo("Pokémon GO raids unchanged; display update skipped.")
        return

    raid_artwork = fetch_raid_artwork(raid_roster)

    frames = render_raid_animation(raid_roster, artwork_by_url=raid_artwork)

    _send_widget_frames(
        client=client,
        panel_index=RAID_PANEL_INDEX,
        frames=frames,
        frame_duration_ms=RAID_FRAME_DURATION_MS if len(frames) > 1 else None,
        name="Pokémon GO raids",
    )

    _write_fingerprint_or_warn(RAID_STATE_PATH, fingerprint)
