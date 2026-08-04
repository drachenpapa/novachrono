from pathlib import Path
from unittest.mock import MagicMock, patch

from novachrono.cli import main
from novachrono.dashboard import CLOCK_PANEL_INDEX
from novachrono.design import PANEL_SIZE


def test_preview_command_creates_preview(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "preview.png"

    exit_code = main(
        [
            "preview",
            "--output",
            str(destination),
        ]
    )

    assert exit_code == 0
    assert destination.exists()


@patch("novachrono.cli.TimesGateClient")
def test_check_device_uses_given_configuration(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.get_configuration.return_value = {
        "ReturnCode": 0,
    }

    exit_code = main(
        [
            "check-device",
            "--host",
            "192.168.178.50",
            "--token",
            "secret",
        ]
    )

    assert exit_code == 0
    mocked_client.get_configuration.assert_called_once_with()


@patch("novachrono.cli.TimesGateClient")
def test_send_clock_targets_center_display(
    mocked_client_class: MagicMock,
) -> None:
    mocked_client = mocked_client_class.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    exit_code = main(
        [
            "send-clock",
            "--host",
            "192.168.178.50",
            "--token",
            "secret",
        ]
    )

    assert exit_code == 0

    call = mocked_client.send_image.call_args

    assert call.kwargs["panel_index"] == CLOCK_PANEL_INDEX
    assert call.kwargs["image"].size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
