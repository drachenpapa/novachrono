"""Novachrono command-line interface."""

import json
from pathlib import Path
from typing import Annotated

import typer

from novachrono.cli._common import (
    HostOption,
    TokenOption,
    _create_times_gate_client,
    _exit_with_error,
    _load_app_config,
    _load_current_weather,
    _load_event_schedule,
    _load_raid_roster,
)
from novachrono.cli.dashboard import send_dashboard
from novachrono.cli.widgets import (
    send_clock,
    send_events,
    send_raids,
    send_weather,
)
from novachrono.dashboard import render_dashboard
from novachrono.outputs.times_gate import TimesGateError
from novachrono.preview import create_preview, save_preview
from novachrono.sources.pokemon_artwork import (
    fetch_event_artwork,
    fetch_raid_artwork,
)

app = typer.Typer(
    name="novachrono",
    help="Render, preview, and send a dashboard for a Divoom Times Gate.",
    no_args_is_help=True,
    add_completion=False,
)


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
    """Render a local preview of the complete dashboard."""

    config = _load_app_config()
    weather = _load_current_weather(config)

    event_schedule = _load_event_schedule(config)
    event_artwork = fetch_event_artwork(event_schedule)

    raid_roster = _load_raid_roster(config)
    raid_artwork = fetch_raid_artwork(raid_roster)

    panels = render_dashboard(
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        event_artwork=event_artwork,
        raid_artwork=raid_artwork,
        timezone=config.timezone,
        locale=config.locale,
        temperature_unit=config.temperature_unit,
    )

    dashboard_preview = create_preview(panels)
    save_preview(dashboard_preview, output)
    typer.echo(f"Dashboard preview written to {output}")


@app.command(name="check-device")
def check_device(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Check the connection to the configured Times Gate."""

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
    typer.echo(json.dumps(response, indent=2, ensure_ascii=False))


app.command(name="send-dashboard")(send_dashboard)
app.command(name="send-clock")(send_clock)
app.command(name="send-pokemon-events")(send_events)
app.command(name="send-pokemon-raids")(send_raids)
app.command(name="send-weather")(send_weather)

__all__ = ["app"]
