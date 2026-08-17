import base64
import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest
from PIL import Image

from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
    encode_image,
)

HOST = "192.168.178.50"
TOKEN = "secret"
API_URL = "http://192.168.178.50:9000/divoom_api"


def _create_panel(
    color: str = "#17132F",
) -> Image.Image:
    return Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
        color=color,
    )


def _create_client() -> TimesGateClient:
    return TimesGateClient(
        TimesGateConfig(
            host=HOST,
            local_token=TOKEN,
        )
    )


def _create_response(
    payload: object,
) -> MagicMock:
    return _create_raw_response(json.dumps(payload))


def _create_raw_response(
    body: str,
) -> MagicMock:
    response = MagicMock()
    response.read.return_value = body.encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def test_config_creates_expected_api_url() -> None:
    config = TimesGateConfig(
        host=HOST,
        local_token=TOKEN,
    )

    assert config.api_url == API_URL


def test_config_strips_host_and_token() -> None:
    config = TimesGateConfig(
        host=f" {HOST} ",
        local_token=f" {TOKEN} ",
    )

    assert config.host == HOST
    assert config.local_token == TOKEN


@pytest.mark.parametrize(
    "host",
    [
        "",
        "   ",
        "http://192.168.178.50",
        "https://192.168.178.50",
    ],
)
def test_config_rejects_invalid_host(
    host: str,
) -> None:
    with pytest.raises(ValueError):
        TimesGateConfig(
            host=host,
            local_token=TOKEN,
        )


def test_config_rejects_empty_token() -> None:
    with pytest.raises(
        ValueError,
        match="local token must not be empty",
    ):
        TimesGateConfig(
            host=HOST,
            local_token=" ",
        )


def test_config_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        TimesGateConfig(
            host=HOST,
            local_token=TOKEN,
            timeout_seconds=0,
        )


def test_encode_image_returns_base64_jpeg() -> None:
    encoded_image = encode_image(_create_panel())
    decoded_image = base64.b64decode(encoded_image)

    with Image.open(io.BytesIO(decoded_image)) as image:
        assert image.format == "JPEG"
        assert image.size == (
            PANEL_SIZE,
            PANEL_SIZE,
        )


@pytest.mark.parametrize(
    "panel_index",
    [-1, PANEL_COUNT],
)
def test_send_image_rejects_invalid_panel_index(
    panel_index: int,
) -> None:
    client = _create_client()

    with pytest.raises(
        ValueError,
        match="Panel index must be between",
    ):
        client.send_image(
            panel_index=panel_index,
            image=_create_panel(),
        )


def test_send_image_rejects_invalid_image_size() -> None:
    client = _create_client()

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


@pytest.mark.parametrize(
    "panel_index",
    [-1, PANEL_COUNT],
)
def test_send_animation_rejects_invalid_panel_index(
    panel_index: int,
) -> None:
    client = _create_client()

    with pytest.raises(
        ValueError,
        match="Panel index must be between",
    ):
        client.send_animation(
            panel_index=panel_index,
            images=(
                _create_panel(),
                _create_panel(),
            ),
            frame_duration_ms=10_000,
        )


def test_send_animation_rejects_empty_animation() -> None:
    client = _create_client()

    with pytest.raises(
        ValueError,
        match="at least one image",
    ):
        client.send_animation(
            panel_index=2,
            images=(),
            frame_duration_ms=10_000,
        )


def test_send_animation_rejects_invalid_frame_duration() -> None:
    client = _create_client()

    with pytest.raises(
        ValueError,
        match="Frame duration must be greater than zero",
    ):
        client.send_animation(
            panel_index=2,
            images=(
                _create_panel(),
                _create_panel(),
            ),
            frame_duration_ms=0,
        )


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_animation_validates_all_images_before_upload(
    mocked_urlopen: MagicMock,
) -> None:
    invalid_image = Image.new(
        mode="RGB",
        size=(64, 64),
    )

    with pytest.raises(
        ValueError,
        match="Image has size",
    ):
        _create_client().send_animation(
            panel_index=2,
            images=(
                _create_panel(),
                invalid_image,
            ),
            frame_duration_ms=10_000,
        )

    mocked_urlopen.assert_not_called()


@patch("novachrono.outputs.times_gate.urlopen")
def test_get_configuration_sends_expected_request(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "Command": "Channel/GetAllConf",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    response = _create_client().get_configuration()

    assert response["ReturnCode"] == 0

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert request.full_url == API_URL

    assert payload == {
        "Command": "Channel/GetAllConf",
        "LocalToken": TOKEN,
    }


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_image_targets_selected_panel(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "Command": "Draw/SendHttpGif",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    _create_client().send_image(
        panel_index=2,
        image=_create_panel(),
    )

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload["Command"] == "Draw/SendHttpGif"
    assert payload["LcdArray"] == [
        0,
        0,
        1,
        0,
        0,
    ]
    assert payload["PicNum"] == 1
    assert payload["PicWidth"] == PANEL_SIZE
    assert payload["PicOffset"] == 0
    assert payload["PicSpeed"] == 1000
    assert isinstance(payload["PicData"], str)


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_animation_sends_native_multi_frame_payload(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "Command": "Draw/SendHttpGif",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    responses = _create_client().send_animation(
        panel_index=3,
        images=(
            _create_panel("#FF0000"),
            _create_panel("#00FF00"),
            _create_panel("#0000FF"),
        ),
        frame_duration_ms=10_000,
    )

    assert len(responses) == 3
    assert mocked_urlopen.call_count == 3

    payloads = [
        json.loads(call.args[0].data.decode("utf-8")) for call in mocked_urlopen.call_args_list
    ]

    picture_ids = {payload["PicID"] for payload in payloads}

    assert len(picture_ids) == 1

    for frame_index, payload in enumerate(payloads):
        assert payload["Command"] == "Draw/SendHttpGif"
        assert payload["LcdArray"] == [
            0,
            0,
            0,
            1,
            0,
        ]
        assert payload["PicNum"] == 3
        assert payload["PicWidth"] == PANEL_SIZE
        assert payload["PicOffset"] == frame_index
        assert payload["PicSpeed"] == 10_000
        assert isinstance(
            payload["PicData"],
            str,
        )


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_animation_uses_different_picture_data_per_frame(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "ReturnCode": 0,
        }
    )

    _create_client().send_animation(
        panel_index=0,
        images=(
            _create_panel("#FF0000"),
            _create_panel("#0000FF"),
        ),
        frame_duration_ms=5_000,
    )

    payloads = [
        json.loads(call.args[0].data.decode("utf-8")) for call in mocked_urlopen.call_args_list
    ]

    assert payloads[0]["PicData"] != payloads[1]["PicData"]


@patch("novachrono.outputs.times_gate.urlopen")
def test_api_error_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "ReturnCode": 7,
            "ReturnMessage": "Invalid token",
        }
    )

    with pytest.raises(
        TimesGateError,
        match="Invalid token",
    ):
        _create_client().get_configuration()


@patch("novachrono.outputs.times_gate.urlopen")
def test_connection_error_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = URLError("Connection refused")

    with pytest.raises(
        TimesGateError,
        match="Could not reach Times Gate",
    ):
        _create_client().get_configuration()


@patch("novachrono.outputs.times_gate.urlopen")
def test_invalid_json_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_raw_response("definitely not json")

    with pytest.raises(
        TimesGateError,
        match="invalid JSON",
    ):
        _create_client().get_configuration()


@patch("novachrono.outputs.times_gate.urlopen")
def test_unexpected_json_structure_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            {
                "ReturnCode": 0,
            }
        ]
    )

    with pytest.raises(
        TimesGateError,
        match="unexpected response",
    ):
        _create_client().get_configuration()
