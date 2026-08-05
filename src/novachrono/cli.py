import json
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    render_dashboard,
)
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
)
from novachrono.preview import create_preview, save_preview

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
        envvar="NOVACHRONO_TIMES_GATE_HOST",
        help=(
            "Times Gate IP address or hostname. Can also be set with NOVACHRONO_TIMES_GATE_HOST."
        ),
        metavar="HOST",
    ),
]

TokenOption = Annotated[
    str | None,
    typer.Option(
        "--token",
        envvar="NOVACHRONO_TIMES_GATE_TOKEN",
        help=("Times Gate local token. Can also be set with NOVACHRONO_TIMES_GATE_TOKEN."),
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
    """Render the complete dashboard preview as a PNG file."""

    panels = render_dashboard()
    dashboard_preview = create_preview(panels)
    save_preview(dashboard_preview, output)

    typer.echo(f"Dashboard preview written to {output}")


@app.command(name="check-device")
def check_device(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Check the connection to the configured Times Gate."""

    client = _create_times_gate_client(
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
    """Render and send the clock to the center display."""

    client = _create_times_gate_client(
        host=host,
        local_token=token,
    )

    panels = render_dashboard()
    clock_panel = panels[CLOCK_PANEL_INDEX]
    display_number = CLOCK_PANEL_INDEX + 1

    typer.echo(f"Sending clock to display {display_number} ...")

    try:
        response = client.send_image(
            panel_index=CLOCK_PANEL_INDEX,
            image=clock_panel,
        )
    except TimesGateError as error:
        _exit_with_error(str(error))

    typer.echo("Clock sent successfully.")
    typer.echo(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        )
    )


@app.command(name="send-dashboard")
def send_dashboard(
    host: HostOption = None,
    token: TokenOption = None,
) -> None:
    """Render and send all five dashboard panels."""

    client = _create_times_gate_client(
        host=host,
        local_token=token,
    )

    panels = render_dashboard()
    failed_displays: list[int] = []

    typer.echo(f"Sending dashboard to {len(panels)} displays at {client.config.api_url} ...")

    for panel_index, panel in enumerate(panels):
        display_number = panel_index + 1

        typer.echo(f"Sending display {display_number}/{len(panels)} ...")

        try:
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


def _create_times_gate_client(
    *,
    host: str | None,
    local_token: str | None,
) -> TimesGateClient:
    missing_variables: list[str] = []

    if host is None:
        missing_variables.append("NOVACHRONO_TIMES_GATE_HOST")

    if local_token is None:
        missing_variables.append("NOVACHRONO_TIMES_GATE_TOKEN")

    if missing_variables:
        joined_variables = ", ".join(missing_variables)
        _exit_with_error(f"Missing required configuration: {joined_variables}")

    try:
        config = TimesGateConfig(
            host=host,
            local_token=local_token,
        )
    except ValueError as error:
        _exit_with_error(str(error))

    return TimesGateClient(config)


def _exit_with_error(message: str) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)
