import typer
from PIL import Image

from novachrono.cli._common import (
    HostOption,
    TokenOption,
    _create_times_gate_client,
    _exit_with_error,
    _load_app_config,
    _load_current_weather,
    _load_event_schedule,
    _load_raw_raid_roster,
    _write_fingerprint_or_warn,
)
from novachrono.dashboard import (
    EVENT_PANEL_INDEX,
    MATRIX_PANEL_INDEX,
    RAID_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
    render_dashboard,
)
from novachrono.display_state import (
    EVENT_STATE_PATH,
    RAID_STATE_PATH,
    WEATHER_STATE_PATH,
    event_schedule_fingerprint,
    raid_roster_fingerprint,
    weather_fingerprint,
)
from novachrono.outputs.delivery import deliver_frames_with_retry
from novachrono.outputs.times_gate import TimesGateError
from novachrono.sources.pokeapi import localize_raid_roster
from novachrono.sources.pokemon_artwork import (
    fetch_event_artwork,
    fetch_raid_artwork,
)
from novachrono.widgets.matrix import (
    MATRIX_FRAME_DURATION_MS,
    render_matrix_animation,
)
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


def send_dashboard(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Retrieve, render, and send all five dashboard panels."""

    app_config = _load_app_config()
    client = _create_times_gate_client(app_config=app_config, host=host, local_token=token)

    weather = _load_current_weather(app_config)
    event_schedule = _load_event_schedule(app_config)
    event_artwork = fetch_event_artwork(event_schedule)
    raw_raid_roster = _load_raw_raid_roster()
    raid_roster = localize_raid_roster(raw_raid_roster, locale=app_config.locale)
    raid_artwork = fetch_raid_artwork(raid_roster)
    event_state = event_schedule_fingerprint(event_schedule, locale=app_config.locale)
    weather_state = weather_fingerprint(
        weather, locale=app_config.locale, temperature_unit=app_config.temperature_unit
    )
    raid_state = raid_roster_fingerprint(raid_roster, locale=app_config.locale)

    panels = render_dashboard(
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        event_artwork=event_artwork,
        raid_artwork=raid_artwork,
        timezone=app_config.timezone,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    matrix_frames = render_matrix_animation()
    event_frames = render_event_animation(
        event_schedule, locale=app_config.locale, artwork_by_url=event_artwork
    )
    weather_frames = render_weather_animation(
        weather, locale=app_config.locale, temperature_unit=app_config.temperature_unit
    )
    raid_frames = render_raid_animation(raid_roster, artwork_by_url=raid_artwork)

    panel_frames: dict[int, tuple[tuple[Image.Image, ...], int | None]] = {
        MATRIX_PANEL_INDEX: (matrix_frames, MATRIX_FRAME_DURATION_MS),
        EVENT_PANEL_INDEX: (
            event_frames,
            EVENT_FRAME_DURATION_MS if len(event_frames) > 1 else None,
        ),
        WEATHER_PANEL_INDEX: (weather_frames, weather_frame_duration_ms(weather.condition)),
        RAID_PANEL_INDEX: (raid_frames, RAID_FRAME_DURATION_MS if len(raid_frames) > 1 else None),
    }

    failed_displays: list[int] = []
    typer.echo(f"Sending dashboard to {len(panels)} displays at {client.config.api_url} ...")

    for panel_index, panel in enumerate(panels):
        display_number = panel_index + 1
        typer.echo(f"Sending display {display_number}/{len(panels)} ...")
        frames, frame_duration_ms = panel_frames.get(panel_index, ((panel,), None))

        try:
            deliver_frames_with_retry(
                client=client,
                panel_index=panel_index,
                frames=frames,
                frame_duration_ms=frame_duration_ms,
            )
        except TimesGateError as error:
            failed_displays.append(display_number)
            typer.echo(f"Display {display_number} failed: {error}", err=True)
            continue

        typer.echo(f"Display {display_number} sent successfully.")

        if panel_index == EVENT_PANEL_INDEX:
            _write_fingerprint_or_warn(EVENT_STATE_PATH, event_state)

        elif panel_index == WEATHER_PANEL_INDEX:
            _write_fingerprint_or_warn(WEATHER_STATE_PATH, weather_state)

        elif panel_index == RAID_PANEL_INDEX:
            _write_fingerprint_or_warn(RAID_STATE_PATH, raid_state)

    if failed_displays:
        formatted_displays = ", ".join(str(display_number) for display_number in failed_displays)
        _exit_with_error(f"Dashboard delivery failed for display(s): {formatted_displays}")

    typer.echo("Dashboard sent successfully.")
