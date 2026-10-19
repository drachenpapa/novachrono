from novachrono.design import PANEL_SIZE
from novachrono.widgets.matrix import (
    MATRIX_FRAME_DURATION_MS,
    render_matrix_animation,
    render_matrix_panel,
)


def test_matrix_frame_duration_is_200_ms() -> None:
    assert MATRIX_FRAME_DURATION_MS == 200


def test_render_matrix_panel_has_expected_size_and_mode() -> None:
    panel = render_matrix_panel()

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
    assert panel.mode == "RGB"


def test_render_matrix_panel_is_deterministic() -> None:
    first = render_matrix_panel()
    second = render_matrix_panel()

    assert first.tobytes() == second.tobytes()


def test_render_matrix_animation_contains_ten_frames() -> None:
    frames = render_matrix_animation()

    assert len(frames) == 10


def test_render_matrix_animation_frames_have_expected_size_and_mode() -> None:
    frames = render_matrix_animation()

    assert all(
        frame.size
        == (
            PANEL_SIZE,
            PANEL_SIZE,
        )
        for frame in frames
    )
    assert all(frame.mode == "RGB" for frame in frames)


def test_render_matrix_animation_contains_different_frames() -> None:
    frames = render_matrix_animation()

    assert len({frame.tobytes() for frame in frames}) > 1


def test_render_matrix_panel_matches_first_animation_frame() -> None:
    panel = render_matrix_panel()
    first_frame = render_matrix_animation()[0]

    assert panel.tobytes() == first_frame.tobytes()
