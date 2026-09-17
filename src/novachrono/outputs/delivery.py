from collections.abc import Callable
from time import sleep
from typing import Any, Final

from PIL import Image

from novachrono.outputs.times_gate import TimesGateClient, TimesGateError

RETRY_DELAY_SECONDS: Final = 5.0

Sleeper = Callable[[float], None]


def deliver_frames(
    *,
    client: TimesGateClient,
    panel_index: int,
    frames: tuple[Image.Image, ...],
    frame_duration_ms: int | None,
) -> tuple[dict[str, Any], ...]:
    """Deliver a static panel or native multi-frame animation."""

    if len(frames) == 1:
        response = client.send_image(
            panel_index=panel_index,
            image=frames[0],
        )

        return (response,)

    if frame_duration_ms is None:
        raise ValueError("Animated panel requires a frame duration")

    return client.send_animation(
        panel_index=panel_index,
        images=frames,
        frame_duration_ms=frame_duration_ms,
    )


def deliver_frames_with_retry(
    *,
    client: TimesGateClient,
    panel_index: int,
    frames: tuple[Image.Image, ...],
    frame_duration_ms: int | None,
    sleeper: Sleeper | None = None,
) -> tuple[dict[str, Any], ...]:
    """Deliver frames and retry once after a temporary device failure."""

    resolved_sleeper = sleep if sleeper is None else sleeper

    try:
        return deliver_frames(
            client=client,
            panel_index=panel_index,
            frames=frames,
            frame_duration_ms=frame_duration_ms,
        )
    except TimesGateError:
        resolved_sleeper(RETRY_DELAY_SECONDS)

        return deliver_frames(
            client=client,
            panel_index=panel_index,
            frames=frames,
            frame_duration_ms=frame_duration_ms,
        )
