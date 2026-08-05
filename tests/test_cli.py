from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from novachrono.cli import app
from novachrono.dashboard import CLOCK_PANEL_INDEX
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.outputs.times_gate import TimesGateError

runner = CliRunner()


def test_help_lists_available_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "preview" in result.stdout
    assert "check-device" in result.stdout
    assert "send-clock" in result.stdout
    assert "send-dashboard" in result.stdout


def test_preview_command_creates_preview(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "preview.png"

    result = runner.invoke(
        app,
        [
            "preview",
            "--output",
            str(destination),
        ],
    )

    assert result.exit_code == 0
    assert destination.is_file()
    assert "Dashboard preview written" in result.stdout


@patch("novachrono.cli.TimesGateClient")
def test_check_device_uses_given_configuration(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.get_configuration.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        [
            "check-device",
            "--host",
            "192.168.178.50",
            "--token",
            "secret",
        ],
    )

    assert result.exit_code == 0
    assert "Connection successful" in result.stdout

    mocked_client_class.assert_called_once()
    mocked_client.get_configuration.assert_called_once_with()


@patch("novachrono.cli.TimesGateClient")
def test_check_device_reads_environment_variables(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.get_configuration.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["check-device"],
        env={
            "NOVACHRONO_TIMES_GATE_HOST": "192.168.178.50",
            "NOVACHRONO_TIMES_GATE_TOKEN": "secret",
        },
    )

    assert result.exit_code == 0

    config = mocked_client_class.call_args.args[0]
    assert config.host == "192.168.178.50"
    assert config.local_token == "secret"


def test_check_device_reports_missing_configuration() -> None:
    result = runner.invoke(
        app,
        ["check-device"],
        env={
            "NOVACHRONO_TIMES_GATE_HOST": "",
            "NOVACHRONO_TIMES_GATE_TOKEN": "",
        },
    )

    assert result.exit_code == 1
    assert "Missing required configuration" in result.stderr
    assert "NOVACHRONO_TIMES_GATE_HOST" in result.stderr
    assert "NOVACHRONO_TIMES_GATE_TOKEN" in result.stderr


@patch("novachrono.cli.TimesGateClient")
def test_send_clock_targets_center_display(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        [
            "send-clock",
            "--host",
            "192.168.178.50",
            "--token",
            "secret",
        ],
    )

    assert result.exit_code == 0
    assert "Clock sent successfully" in result.stdout

    call = mocked_client.send_image.call_args

    assert call.kwargs["panel_index"] == CLOCK_PANEL_INDEX
    assert call.kwargs["image"].size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )


@patch("novachrono.cli.TimesGateClient")
def test_send_dashboard_sends_all_panels(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        [
            "send-dashboard",
            "--host",
            "192.168.178.50",
            "--token",
            "secret",
        ],
    )

    assert result.exit_code == 0
    assert "Dashboard sent successfully" in result.stdout
    assert mocked_client.send_image.call_count == PANEL_COUNT

    calls = mocked_client.send_image.call_args_list

    assert [call.kwargs["panel_index"] for call in calls] == list(range(PANEL_COUNT))

    assert all(
        call.kwargs["image"].size
        == (
            PANEL_SIZE,
            PANEL_SIZE,
        )
        for call in calls
    )


@patch("novachrono.cli.TimesGateClient")
def test_send_dashboard_continues_after_panel_failure(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.send_image.side_effect = [
        {"ReturnCode": 0},
        TimesGateError("Connection interrupted"),
        {"ReturnCode": 0},
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    ]

    result = runner.invoke(
        app,
        [
            "send-dashboard",
            "--host",
            "192.168.178.50",
            "--token",
            "secret",
        ],
    )

    assert result.exit_code == 1
    assert mocked_client.send_image.call_count == PANEL_COUNT

    assert "Display 2 failed" in result.stderr
    assert "Connection interrupted" in result.stderr
    assert "Dashboard delivery failed for display(s): 2" in result.stderr

    assert "Display 1 sent successfully" in result.stdout
    assert "Display 3 sent successfully" in result.stdout
    assert "Display 4 sent successfully" in result.stdout
    assert "Display 5 sent successfully" in result.stdout
