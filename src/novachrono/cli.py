import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer
from PIL import Image

from novachrono.config import AppConfig, ConfigError, load_config
from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    POKEMON_GO_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
    render_dashboard,
)
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
)
from novachrono.pokemon_go import RaidRoster
from novachrono.preview import create_preview, save_preview
from novachrono.sources.open_meteo import (
    OpenMeteoError,
    fetch_current_weather,
)
from novachrono.sources.pokeapi import localize_raid_roster
from novachrono.sources.pokemon_artwork import fetch_raid_artwork
from novachrono.sources.scraped_duck import (
    ScrapedDuckError,
    fetch_raid_roster,
)
from novachrono.weather import CurrentWeather
from novachrono.widgets.clock import render_clock_panel
from novachrono.widgets.pokemon_go import render_raid_animation
from novachrono.widgets.weather import render_weather_panel

POKEMON_GO_FRAME_DURATION_MS: Final = 10_000

app = typer.Typer(
    name="novachrono",
    help="Render and send dashboards to a Divoom Times Gate.",
    no_args_is_help=True,
    add_completion=False,
)

HostOption = Annotated[
    str | None,
    typer.Option(
        "--host",
        help=("Override the Times Gate host configured with NOVACHRONO_TIMES_GATE_HOST."),
        metavar="HOST",
    ),
]

TokenOption = Annotated[
    str | None,
    typer.Option(
        "--token",
        help=("Override the Times Gate token configured with NOVACHRONO_TIMES_GATE_TOKEN."),
        metavar="TOKEN",
    ),
]


@app.command()
def preview(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Destination for the generated dashboard preview.",
            dir_okay=False,
        ),
    ] = Path("output/dashboard-preview.png"),
) -> None:
    """Render the complete dashboard preview."""

    config = _load_app_config()

    weather = _load_current_weather(config)
    raid_roster = _load_raid_roster(config)
    raid_artwork = fetch_raid_artwork(raid_roster)

    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
        raid_artwork=raid_artwork,
        timezone=config.timezone,
        locale=config.locale,
        temperature_unit=config.temperature_unit,
    )

    dashboard_preview = create_preview(panels)
    save_preview(
        dashboard_preview,
        output,
    )

    typer.echo(f"Dashboard preview written to {output}")


@app.command(name="check-device")
def check_device(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Check the configured Times Gate connection."""

    app_config = _load_app_config()

    client = _create_times_gate_client(
        app_config=app_config,
        host=host,
        local_token=token,
    )

    typer.echo(f"Connecting to {client.config.api_url} ...")

    try:
        response = client.get_configuration()
    except TimesGateError as error:
        _exit_with_error(str(error))

    typer.echo("Connection successful.")
    typer.echo(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        )
    )


@app.command(name="send-clock")
def send_clock(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Render and send the clock panel."""

    app_config = _load_app_config()

    client = _create_times_gate_client(
        app_config=app_config,
        host=host,
        local_token=token,
    )

    panel = render_clock_panel(datetime.now(app_config.timezone))

    _send_single_panel(
        client=client,
        panel_index=CLOCK_PANEL_INDEX,
        panel=panel,
        name="Clock",
    )


@app.command(name="send-weather")
def send_weather(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Retrieve, render, and send the weather panel."""

    app_config = _load_app_config()

    client = _create_times_gate_client(
        app_config=app_config,
        host=host,
        local_token=token,
    )

    weather = _load_current_weather(app_config)

    panel = render_weather_panel(
        weather,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    _send_single_panel(
        client=client,
        panel_index=WEATHER_PANEL_INDEX,
        panel=panel,
        name="Weather",
    )


@app.command(name="send-pokemon")
def send_pokemon(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Retrieve, render, and send the Pokémon GO raid panel."""

    app_config = _load_app_config()

    client = _create_times_gate_client(
        app_config=app_config,
        host=host,
        local_token=token,
    )

    raid_roster = _load_raid_roster(app_config)
    raid_artwork = fetch_raid_artwork(raid_roster)

    frames = render_raid_animation(
        raid_roster,
        artwork_by_url=raid_artwork,
    )

    _send_pokemon_frames(
        client=client,
        frames=frames,
    )


@app.command(name="send-dashboard")
def send_dashboard(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Retrieve, render, and send all five dashboard panels."""

    app_config = _load_app_config()

    client = _create_times_gate_client(
        app_config=app_config,
        host=host,
        local_token=token,
    )

    weather = _load_current_weather(app_config)
    raid_roster = _load_raid_roster(app_config)
    raid_artwork = fetch_raid_artwork(raid_roster)

    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
        raid_artwork=raid_artwork,
        timezone=app_config.timezone,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    pokemon_frames = render_raid_animation(
        raid_roster,
        artwork_by_url=raid_artwork,
    )

    failed_displays: list[int] = []

    typer.echo(f"Sending dashboard to {len(panels)} displays at {client.config.api_url} ...")

    for panel_index, panel in enumerate(panels):
        display_number = panel_index + 1

        typer.echo(f"Sending display {display_number}/{len(panels)} ...")

        try:
            if panel_index == POKEMON_GO_PANEL_INDEX and len(pokemon_frames) > 1:
                client.send_animation(
                    panel_index=panel_index,
                    images=pokemon_frames,
                    frame_duration_ms=POKEMON_GO_FRAME_DURATION_MS,
                )
            else:
                client.send_image(
                    panel_index=panel_index,
                    image=panel,
                )
        except TimesGateError as error:
            failed_displays.append(display_number)

            typer.echo(
                f"Display {display_number} failed: {error}",
                err=True,
            )
            continue

        typer.echo(f"Display {display_number} sent successfully.")

    if failed_displays:
        formatted_displays = ", ".join(str(display_number) for display_number in failed_displays)

        _exit_with_error(f"Dashboard delivery failed for display(s): {formatted_displays}")

    typer.echo("Dashboard sent successfully.")


def _send_pokemon_frames(
    *,
    client: TimesGateClient,
    frames: tuple[Image.Image, ...],
) -> None:
    display_number = POKEMON_GO_PANEL_INDEX + 1

    typer.echo(f"Sending Pokémon GO to display {display_number} ...")

    try:
        if len(frames) == 1:
            response = client.send_image(
                panel_index=POKEMON_GO_PANEL_INDEX,
                image=frames[0],
            )

            responses = (response,)
        else:
            responses = client.send_animation(
                panel_index=POKEMON_GO_PANEL_INDEX,
                images=frames,
                frame_duration_ms=POKEMON_GO_FRAME_DURATION_MS,
            )
    except TimesGateError as error:
        _exit_with_error(str(error))

    typer.echo(f"Pokémon GO sent successfully with {len(frames)} frame(s).")

    typer.echo(
        json.dumps(
            responses,
            indent=2,
            ensure_ascii=False,
        )
    )


def _send_single_panel(
    *,
    client: TimesGateClient,
    panel_index: int,
    panel: Image.Image,
    name: str,
) -> None:
    display_number = panel_index + 1

    typer.echo(f"Sending {name.lower()} to display {display_number} ...")

    try:
        response = client.send_image(
            panel_index=panel_index,
            image=panel,
        )
    except TimesGateError as error:
        _exit_with_error(str(error))

    typer.echo(f"{name} sent successfully.")

    typer.echo(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        )
    )


def _load_current_weather(
    app_config: AppConfig,
) -> CurrentWeather:
    latitude = app_config.weather.latitude
    longitude = app_config.weather.longitude

    if latitude is None or longitude is None:
        missing_variables: list[str] = []

        if latitude is None:
            missing_variables.append("NOVACHRONO_WEATHER_LATITUDE")

        if longitude is None:
            missing_variables.append("NOVACHRONO_WEATHER_LONGITUDE")

        joined_variables = ", ".join(missing_variables)

        _exit_with_error(f"Missing required weather configuration: {joined_variables}")

    try:
        return fetch_current_weather(
            latitude=latitude,
            longitude=longitude,
            timezone=app_config.timezone,
        )
    except OpenMeteoError as error:
        _exit_with_error(str(error))


def _load_raid_roster(
    app_config: AppConfig,
) -> RaidRoster:
    try:
        roster = fetch_raid_roster()
    except ScrapedDuckError as error:
        _exit_with_error(str(error))

    return localize_raid_roster(
        roster,
        locale=app_config.locale,
    )


def _load_app_config() -> AppConfig:
    try:
        return load_config()
    except ConfigError as error:
        _exit_with_error(str(error))


def _create_times_gate_client(
    *,
    app_config: AppConfig,
    host: str | None,
    local_token: str | None,
) -> TimesGateClient:
    resolved_host = _resolve_value(
        override=host,
        configured=app_config.times_gate.host,
    )

    resolved_token = _resolve_value(
        override=local_token,
        configured=app_config.times_gate.local_token,
    )

    if resolved_host is None or resolved_token is None:
        missing_variables: list[str] = []

        if resolved_host is None:
            missing_variables.append("NOVACHRONO_TIMES_GATE_HOST")

        if resolved_token is None:
            missing_variables.append("NOVACHRONO_TIMES_GATE_TOKEN")

        joined_variables = ", ".join(missing_variables)

        _exit_with_error(f"Missing required configuration: {joined_variables}")

    try:
        times_gate_config = TimesGateConfig(
            host=resolved_host,
            local_token=resolved_token,
        )
    except ValueError as error:
        _exit_with_error(str(error))

    return TimesGateClient(times_gate_config)


def _resolve_value(
    *,
    override: str | None,
    configured: str | None,
) -> str | None:
    if override is None:
        return configured

    normalized_override = override.strip()

    if normalized_override:
        return normalized_override

    return configured


def _exit_with_error(
    message: str,
) -> NoReturn:
    typer.echo(
        f"Error: {message}",
        err=True,
    )

    raise typer.Exit(code=1)
