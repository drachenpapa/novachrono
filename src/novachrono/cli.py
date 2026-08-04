import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

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


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the Novachrono command-line interface."""

    parser = _create_parser()
    parsed_arguments = parser.parse_args(arguments)

    try:
        return parsed_arguments.handler(parsed_arguments)
    except KeyError as error:
        variable_name = error.args[0]
        parser.error(f"Required environment variable is missing: {variable_name}")
    except (TimesGateError, ValueError) as error:
        parser.error(str(error))

    return 2


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novachrono",
        description="Render and send dashboards to a Divoom Times Gate.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    preview_parser = subparsers.add_parser(
        "preview",
        help="Render a dashboard preview as a PNG file.",
    )
    preview_parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/dashboard-preview.png"),
        help=("Destination for the preview image (default: output/dashboard-preview.png)."),
    )
    preview_parser.set_defaults(handler=_run_preview)

    check_parser = subparsers.add_parser(
        "check-device",
        help="Check the connection to the configured Times Gate.",
    )
    _add_device_arguments(check_parser)
    check_parser.set_defaults(handler=_run_check_device)

    send_clock_parser = subparsers.add_parser(
        "send-clock",
        help="Render and send the clock to the center display.",
    )
    _add_device_arguments(send_clock_parser)
    send_clock_parser.set_defaults(handler=_run_send_clock)

    return parser


def _add_device_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--host",
        help=("Times Gate IP address or hostname. Defaults to NOVACHRONO_TIMES_GATE_HOST."),
    )
    parser.add_argument(
        "--token",
        help=("Times Gate local token. Defaults to NOVACHRONO_TIMES_GATE_TOKEN."),
    )


def _run_preview(arguments: argparse.Namespace) -> int:
    panels = render_dashboard()
    preview = create_preview(panels)

    destination: Path = arguments.output
    save_preview(preview, destination)

    print(f"Dashboard preview written to {destination}")
    return 0


def _run_check_device(arguments: argparse.Namespace) -> int:
    client = _create_times_gate_client(arguments)

    print(f"Connecting to {client.config.api_url} ...")

    response = client.get_configuration()

    print("Connection successful.")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    return 0


def _run_send_clock(arguments: argparse.Namespace) -> int:
    client = _create_times_gate_client(arguments)

    panels = render_dashboard()
    clock_panel = panels[CLOCK_PANEL_INDEX]

    display_number = CLOCK_PANEL_INDEX + 1
    print(f"Sending clock to display {display_number} ...")

    response = client.send_image(
        panel_index=CLOCK_PANEL_INDEX,
        image=clock_panel,
    )

    print("Clock sent successfully.")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    return 0


def _create_times_gate_client(
    arguments: argparse.Namespace,
) -> TimesGateClient:
    host = arguments.host or os.environ["NOVACHRONO_TIMES_GATE_HOST"]
    local_token = arguments.token or os.environ["NOVACHRONO_TIMES_GATE_TOKEN"]

    config = TimesGateConfig(
        host=host,
        local_token=local_token,
    )

    return TimesGateClient(config)
