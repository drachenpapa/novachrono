import base64
import io
import json
from http.server import ThreadingHTTPServer
from threading import Event, Thread
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest
from PIL import Image

from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
    _create_gif_request_handler,
    encode_image,
)

HOST = "192.168.178.50"
TOKEN = "secret"

API_URL_400 = "http://192.168.178.50/post"
API_URL_402 = "http://192.168.178.50:9000/divoom_api"

LOCAL_ADDRESS = "192.168.178.25"
LOCAL_GIF_PORT = 43210
LOCAL_GIF_URL = f"http://{LOCAL_ADDRESS}:{LOCAL_GIF_PORT}/novachrono.gif"


def _create_panel(
    color: str = "#17132F",
) -> Image.Image:
    return Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
        color=color,
    )


def _create_client(
    hardware_version: int = 402,
) -> TimesGateClient:
    return TimesGateClient(
        TimesGateConfig(
            host=HOST,
            local_token=TOKEN,
            hardware_version=hardware_version,
        )
    )


def _create_response(
    payload: object,
) -> MagicMock:
    return _create_raw_response(json.dumps(payload))


def _create_raw_response(
    body: str,
) -> MagicMock:
    return _create_bytes_response(body.encode("utf-8"))


def _create_bytes_response(
    body: bytes,
) -> MagicMock:
    response = MagicMock()
    response.read.return_value = body

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def _configure_play_gif_mocks(
    mocked_event_class: MagicMock,
    mocked_server_class: MagicMock,
) -> tuple[MagicMock, MagicMock]:
    fetched = mocked_event_class.return_value
    fetched.wait.return_value = True

    server = mocked_server_class.return_value
    server.server_address = (
        LOCAL_ADDRESS,
        LOCAL_GIF_PORT,
    )

    return fetched, server


def test_config_creates_expected_api_url_for_hardware_402() -> None:
    config = TimesGateConfig(
        host=HOST,
        local_token=TOKEN,
        hardware_version=402,
    )

    assert config.api_url == API_URL_402


def test_config_creates_expected_api_url_for_hardware_400() -> None:
    config = TimesGateConfig(
        host=HOST,
        local_token=TOKEN,
        hardware_version=400,
    )

    assert config.api_url == API_URL_400


def test_config_uses_hardware_402_by_default() -> None:
    config = TimesGateConfig(
        host=HOST,
        local_token=TOKEN,
    )

    assert config.hardware_version == 402
    assert config.api_url == API_URL_402


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
        f"{HOST}:9000",
        f"{HOST}/divoom_api",
        f"{HOST}?mode=test",
        f"{HOST}#fragment",
        "times gate.local",
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


@pytest.mark.parametrize(
    "hardware_version",
    [
        0,
        399,
        401,
        403,
    ],
)
def test_config_rejects_unsupported_hardware_version(
    hardware_version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported Times Gate hardware version",
    ):
        TimesGateConfig(
            host=HOST,
            local_token=TOKEN,
            hardware_version=hardware_version,
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

    assert request.full_url == API_URL_402

    assert payload == {
        "Command": "Channel/GetAllConf",
        "LocalToken": TOKEN,
    }


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_image_targets_selected_panel_for_hardware_402(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "Command": "Draw/SendHttpGif",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    _create_client(hardware_version=402).send_image(
        panel_index=2,
        image=_create_panel(),
    )

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert request.full_url == API_URL_402

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
    assert isinstance(
        payload["PicData"],
        str,
    )


@patch("novachrono.outputs.times_gate.urlopen")
def test_send_animation_sends_native_multi_frame_payload_for_hardware_402(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "Command": "Draw/SendHttpGif",
            "ReturnCode": 0,
            "ReturnMessage": "",
        }
    )

    responses = _create_client(hardware_version=402).send_animation(
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
def test_send_animation_uses_different_picture_data_per_frame_for_hardware_402(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        {
            "ReturnCode": 0,
        }
    )

    _create_client(hardware_version=402).send_animation(
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
def test_send_animation_reports_failed_frame_for_hardware_402(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = [
        _create_response(
            {
                "ReturnCode": 0,
            }
        ),
        URLError("Connection refused"),
    ]

    with pytest.raises(
        TimesGateError,
        match="animation frame 2/3",
    ):
        _create_client(hardware_version=402).send_animation(
            panel_index=2,
            images=(
                _create_panel("#FF0000"),
                _create_panel("#00FF00"),
                _create_panel("#0000FF"),
            ),
            frame_duration_ms=5_000,
        )

    assert mocked_urlopen.call_count == 2


def test_gif_request_handler_serves_gif_and_marks_fetch() -> None:
    gif_data = b"test-gif-data"
    fetched = Event()

    handler = _create_gif_request_handler(
        gif_data,
        fetched,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler,
    )

    server_thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    server_thread.start()

    host, port = server.server_address

    try:
        with urlopen(  # nosec B310 - loopback-only test server
            f"http://{host}:{port}/novachrono.gif",
            timeout=2.0,
        ) as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "image/gif"
            assert response.read() == gif_data

        assert fetched.wait(timeout=1.0)
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1.0)


def test_send_image_uses_play_gif_for_hardware_400() -> None:
    with (
        patch("novachrono.outputs.times_gate.urlopen") as mocked_urlopen,
        patch(
            "novachrono.outputs.times_gate._resolve_local_address",
            return_value=LOCAL_ADDRESS,
        ),
        patch("novachrono.outputs.times_gate.Event") as mocked_event_class,
        patch(
            "novachrono.outputs.times_gate._create_gif_request_handler"
        ) as mocked_handler_factory,
        patch("novachrono.outputs.times_gate.ThreadingHTTPServer") as mocked_server_class,
        patch("novachrono.outputs.times_gate.Thread") as mocked_thread_class,
    ):
        mocked_urlopen.return_value = _create_response(
            {
                "Command": "Device/PlayGif",
                "ReturnCode": 0,
                "ReturnMessage": "",
            }
        )

        fetched, server = _configure_play_gif_mocks(
            mocked_event_class,
            mocked_server_class,
        )

        handler = MagicMock()
        mocked_handler_factory.return_value = handler

        response = _create_client(hardware_version=400).send_image(
            panel_index=1,
            image=_create_panel(),
        )

    assert response["ReturnCode"] == 0

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert request.full_url == API_URL_400

    assert payload == {
        "Command": "Device/PlayGif",
        "LocalToken": TOKEN,
        "LcdArray": [
            0,
            1,
            0,
            0,
            0,
        ],
        "FileName": [
            LOCAL_GIF_URL,
        ],
    }

    gif_data = mocked_handler_factory.call_args.args[0]

    with Image.open(io.BytesIO(gif_data)) as image:
        assert image.format == "GIF"
        assert image.n_frames == 1
        assert image.size == (
            PANEL_SIZE,
            PANEL_SIZE,
        )

    fetched.wait.assert_called_once_with(timeout=8.0)

    mocked_server_class.assert_called_once_with(
        (
            LOCAL_ADDRESS,
            0,
        ),
        handler,
    )

    mocked_thread_class.assert_called_once_with(
        target=server.serve_forever,
        daemon=True,
    )

    mocked_thread_class.return_value.start.assert_called_once()

    server.shutdown.assert_called_once()
    server.server_close.assert_called_once()
    mocked_thread_class.return_value.join.assert_called_once_with(timeout=1.0)


def test_send_animation_uses_multi_frame_gif_for_hardware_400() -> None:
    with (
        patch("novachrono.outputs.times_gate.urlopen") as mocked_urlopen,
        patch(
            "novachrono.outputs.times_gate._resolve_local_address",
            return_value=LOCAL_ADDRESS,
        ),
        patch("novachrono.outputs.times_gate.Event") as mocked_event_class,
        patch(
            "novachrono.outputs.times_gate._create_gif_request_handler"
        ) as mocked_handler_factory,
        patch("novachrono.outputs.times_gate.ThreadingHTTPServer") as mocked_server_class,
        patch("novachrono.outputs.times_gate.Thread"),
    ):
        mocked_urlopen.return_value = _create_response(
            {
                "Command": "Device/PlayGif",
                "ReturnCode": 0,
            }
        )

        _configure_play_gif_mocks(
            mocked_event_class,
            mocked_server_class,
        )

        responses = _create_client(hardware_version=400).send_animation(
            panel_index=4,
            images=(
                _create_panel("#FF0000"),
                _create_panel("#00FF00"),
                _create_panel("#0000FF"),
            ),
            frame_duration_ms=5_000,
        )

    assert responses == (
        {
            "Command": "Device/PlayGif",
            "ReturnCode": 0,
        },
    )

    assert mocked_urlopen.call_count == 1

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert request.full_url == API_URL_400

    assert payload == {
        "Command": "Device/PlayGif",
        "LocalToken": TOKEN,
        "LcdArray": [
            0,
            0,
            0,
            0,
            1,
        ],
        "FileName": [
            LOCAL_GIF_URL,
        ],
    }

    gif_data = mocked_handler_factory.call_args.args[0]

    with Image.open(io.BytesIO(gif_data)) as image:
        assert image.format == "GIF"
        assert image.n_frames == 3
        assert image.info["duration"] == 5_000

        image.seek(0)
        first_frame = image.convert("RGB").getpixel((0, 0))

        image.seek(1)
        second_frame = image.convert("RGB").getpixel((0, 0))

        image.seek(2)
        third_frame = image.convert("RGB").getpixel((0, 0))

    assert first_frame != second_frame
    assert second_frame != third_frame
    assert first_frame != third_frame


def test_play_gif_fails_when_hardware_400_does_not_fetch_gif() -> None:
    with (
        patch("novachrono.outputs.times_gate.urlopen") as mocked_urlopen,
        patch(
            "novachrono.outputs.times_gate._resolve_local_address",
            return_value=LOCAL_ADDRESS,
        ),
        patch("novachrono.outputs.times_gate.Event") as mocked_event_class,
        patch("novachrono.outputs.times_gate._create_gif_request_handler"),
        patch("novachrono.outputs.times_gate.ThreadingHTTPServer") as mocked_server_class,
        patch("novachrono.outputs.times_gate.Thread") as mocked_thread_class,
    ):
        mocked_urlopen.return_value = _create_response(
            {
                "Command": "Device/PlayGif",
                "ReturnCode": 0,
            }
        )

        fetched, server = _configure_play_gif_mocks(
            mocked_event_class,
            mocked_server_class,
        )
        fetched.wait.return_value = False

        with pytest.raises(
            TimesGateError,
            match="did not fetch the GIF",
        ):
            _create_client(hardware_version=400).send_image(
                panel_index=0,
                image=_create_panel(),
            )

    fetched.wait.assert_called_once_with(timeout=8.0)

    server.shutdown.assert_called_once()
    server.server_close.assert_called_once()
    mocked_thread_class.return_value.join.assert_called_once_with(timeout=1.0)


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
def test_http_error_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = HTTPError(
        url=API_URL_402,
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None,
    )

    with pytest.raises(
        TimesGateError,
        match="HTTP 401",
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
def test_timeout_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = TimeoutError()

    with pytest.raises(
        TimesGateError,
        match="timed out",
    ):
        _create_client().get_configuration()


@patch("novachrono.outputs.times_gate.urlopen")
def test_invalid_utf8_raises_times_gate_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_bytes_response(b"\xff")

    with pytest.raises(
        TimesGateError,
        match="invalid UTF-8 response",
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
