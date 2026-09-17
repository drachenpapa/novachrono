from unittest.mock import MagicMock

import pytest
from PIL import Image

from novachrono.design import PANEL_SIZE
from novachrono.outputs.delivery import (
    RETRY_DELAY_SECONDS,
    deliver_frames,
    deliver_frames_with_retry,
)
from novachrono.outputs.times_gate import TimesGateError

FRAME_DURATION_MS = 10_000


def test_deliver_frames_sends_single_frame_as_static_image() -> None:
    client = MagicMock()
    client.send_image.return_value = {
        "ReturnCode": 0,
    }

    panel = _create_panel()

    responses = deliver_frames(
        client=client,
        panel_index=2,
        frames=(panel,),
        frame_duration_ms=None,
    )

    assert responses == (
        {
            "ReturnCode": 0,
        },
    )

    client.send_image.assert_called_once_with(
        panel_index=2,
        image=panel,
    )

    client.send_animation.assert_not_called()


def test_deliver_frames_sends_multiple_frames_as_animation() -> None:
    client = MagicMock()

    expected_responses = (
        {
            "ReturnCode": 0,
        },
        {
            "ReturnCode": 0,
        },
    )

    client.send_animation.return_value = expected_responses

    frames = (
        _create_panel(),
        _create_panel(),
    )

    responses = deliver_frames(
        client=client,
        panel_index=3,
        frames=frames,
        frame_duration_ms=FRAME_DURATION_MS,
    )

    assert responses == expected_responses

    client.send_animation.assert_called_once_with(
        panel_index=3,
        images=frames,
        frame_duration_ms=FRAME_DURATION_MS,
    )

    client.send_image.assert_not_called()


def test_deliver_frames_requires_duration_for_animation() -> None:
    with pytest.raises(
        ValueError,
        match="Animated panel requires a frame duration",
    ):
        deliver_frames(
            client=MagicMock(),
            panel_index=1,
            frames=(
                _create_panel(),
                _create_panel(),
            ),
            frame_duration_ms=None,
        )


def test_deliver_frames_with_retry_retries_once() -> None:
    client = MagicMock()

    client.send_image.side_effect = [
        TimesGateError("Connection failed"),
        {
            "ReturnCode": 0,
        },
    ]

    sleeper = MagicMock()
    panel = _create_panel()

    responses = deliver_frames_with_retry(
        client=client,
        panel_index=2,
        frames=(panel,),
        frame_duration_ms=None,
        sleeper=sleeper,
    )

    assert responses == (
        {
            "ReturnCode": 0,
        },
    )

    assert client.send_image.call_count == 2
    sleeper.assert_called_once_with(RETRY_DELAY_SECONDS)


def test_deliver_frames_with_retry_raises_after_second_failure() -> None:
    client = MagicMock()
    client.send_image.side_effect = TimesGateError("Connection failed")

    sleeper = MagicMock()

    with pytest.raises(
        TimesGateError,
        match="Connection failed",
    ):
        deliver_frames_with_retry(
            client=client,
            panel_index=2,
            frames=(_create_panel(),),
            frame_duration_ms=None,
            sleeper=sleeper,
        )

    assert client.send_image.call_count == 2
    sleeper.assert_called_once_with(RETRY_DELAY_SECONDS)


def _create_panel() -> Image.Image:
    return Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
    )
