import base64
import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest
from PIL import Image

from novachrono.design import PANEL_SIZE
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
    encode_image,
)


def create_panel() -> Image.Image:
    return Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
        color="#17132F",
    )


def create_response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def test_config_creates_expected_api_url() -> None:
    config = TimesGateConfig(
        host="192.168.178.50",
        local_token="secret",
    )

    assert config.api_url == "http://192.168.178.50:9000/divoom_api"


def test_config_strips_host_and_token() -> None:
    config = TimesGateConfig(
        host=" 192.168.178.50 ",
        local_token=" secret ",
    )

    assert config.host == "192.168.178.50"
    assert config.local_token == "secret"


@pytest.mark.parametrize(
    "host",
    [
        "",
        "   ",
        "http://192.168.178.50",
        "https://192.168.178.50",
    ],
)
def test_config_rejects_invalid_host(host: str) -> None:
    with pytest.raises(ValueError):
        TimesGateConfig(
            host=host,
            local_token="secret",
        )


def test_config_rejects_empty_token() -> None:
    with pytest.raises(
        ValueError,
        match="local token must not be empty",
    ):
        TimesGateConfig(
            host="192.168.178.50",
            local_token=" ",
        )


def test_config_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
            timeout_seconds=0,
        )


def test_encode_image_returns_base64_jpeg() -> None:
    encoded_image = encode_image(create_panel())

    decoded_image = base64.b64decode(encoded_image)

    with Image.open(io.BytesIO(decoded_image)) as image:
        assert image.format == "JPEG"
        assert image.size == (PANEL_SIZE, PANEL_SIZE)


def test_send_image_rejects_invalid_panel_index() -> None:
    client = TimesGateClient(
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
        )
    )

    with pytest.raises(
        ValueError,
        match="Panel index must be between",
    ):
        client.send_image(
            panel_index=5,
            image=create_panel(),
        )


def test_send_image_rejects_invalid_image_size() -> None:
    client = TimesGateClient(
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
        )
    )

    invalid_image = Image.new(
        mode="RGB",
        size=(64, 64),
    )

    with pytest.raises(
        ValueError,
        match="Image has size",
    ):
        client.send_image(
            panel_index=2,
            image=invalid_image,
        )


@patch("novachrono.outputs.times_gate.urlopen")
def test_get_configuration_sends_expected_request(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = create_response(
        {
            "Command": "Channel/GetAllConf",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    client = TimesGateClient(
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
        )
    )

    response = client.get_configuration()

    assert response["ReturnCode"] == 0

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert request.full_url == ("http://192.168.178.50:9000/divoom_api")
    assert payload == {
        "Command": "Channel/GetAllConf",
        "LocalToken": "secret",
    }


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_image_targets_selected_panel(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = create_response(
        {
            "Command": "Draw/SendHttpGif",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    client = TimesGateClient(
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
        )
    )

    client.send_image(
        panel_index=2,
        image=create_panel(),
    )

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload["Command"] == "Draw/SendHttpGif"
    assert payload["LcdArray"] == [0, 0, 1, 0, 0]
    assert payload["PicWidth"] == PANEL_SIZE
    assert isinstance(payload["PicData"], str)


@patch("novachrono.outputs.times_gate.urlopen")
def test_api_error_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = create_response(
        {
            "ReturnCode": 7,
            "ReturnMessage": "Invalid token",
        }
    )

    client = TimesGateClient(
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
        )
    )

    with pytest.raises(
        TimesGateError,
        match="Invalid token",
    ):
        client.get_configuration()


@patch("novachrono.outputs.times_gate.urlopen")
def test_connection_error_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = URLError("Connection refused")

    client = TimesGateClient(
        TimesGateConfig(
            host="192.168.178.50",
            local_token="secret",
        )
    )

    with pytest.raises(
        TimesGateError,
        match="Could not reach Times Gate",
    ):
        client.get_configuration()
