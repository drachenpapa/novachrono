from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from novachrono.cli import app
from novachrono.config import AppConfig, WeatherSettings
from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    EVENT_PANEL_INDEX,
    RAID_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
)
from novachrono.models.pokemon_go import EventSchedule, RaidRoster
from novachrono.models.weather import CurrentWeather, WeatherCondition
from novachrono.outputs.times_gate import TimesGateError
from novachrono.sources.open_meteo import OpenMeteoError
from novachrono.sources.scraped_duck import ScrapedDuckError

runner = CliRunner()


@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_clock_fetches_no_external_data(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_load_events: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = replace(
        app_config,
        weather=WeatherSettings(
            latitude=None,
            longitude=None,
        ),
    )

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-clock"],
    )

    assert result.exit_code == 0

    mocked_load_weather.assert_not_called()
    mocked_load_raids.assert_not_called()
    mocked_load_events.assert_not_called()

    mocked_client.send_image.assert_called_once()
    mocked_client.send_animation.assert_not_called()

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == CLOCK_PANEL_INDEX

    assert "1 frame(s)" in result.stdout


@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_reports_missing_weather_configuration(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = replace(
        app_config,
        weather=WeatherSettings(
            latitude=None,
            longitude=None,
        ),
    )

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 1
    assert "NOVACHRONO_WEATHER_LATITUDE" in result.stderr
    assert "NOVACHRONO_WEATHER_LONGITUDE" in result.stderr

    mocked_client = mocked_create_client.return_value

    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_not_called()


@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_targets_weather_display_only(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_load_events: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    state_paths: dict[str, Path],
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 0

    mocked_load_raids.assert_not_called()
    mocked_load_events.assert_not_called()
    mocked_client.send_animation.assert_not_called()

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == WEATHER_PANEL_INDEX

    assert state_paths["weather"].is_file()


@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_skips_unchanged_weather(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-weather"],
    )

    second_result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    assert mocked_client.send_image.call_count == 1

    assert "Weather unchanged; display update skipped." in second_result.stdout


@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_force_sends_unchanged_weather(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-weather"],
    )

    forced_result = runner.invoke(
        app,
        [
            "send-weather",
            "--force",
        ],
    )

    assert first_result.exit_code == 0
    assert forced_result.exit_code == 0
    assert mocked_client.send_image.call_count == 2


@pytest.mark.parametrize(
    (
        "condition",
        "expected_frame_count",
        "expected_duration_ms",
    ),
    [
        (
            WeatherCondition.RAIN,
            3,
            350,
        ),
        (
            WeatherCondition.FOG,
            10,
            500,
        ),
    ],
)
@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_uses_animation_for_animated_conditions(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    condition: WeatherCondition,
    expected_frame_count: int,
    expected_duration_ms: int,
) -> None:
    animated_weather = replace(
        weather,
        condition=condition,
    )

    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = animated_weather

    mocked_client = mocked_create_client.return_value
    mocked_client.send_animation.return_value = tuple(
        {"ReturnCode": 0} for _ in range(expected_frame_count)
    )

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 0

    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == WEATHER_PANEL_INDEX
    assert len(arguments["images"]) == expected_frame_count
    assert arguments["frame_duration_ms"] == expected_duration_ms


@patch("novachrono.cli.widgets.fetch_event_artwork")
@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_events_uses_static_image_for_single_frame(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    event_schedule: EventSchedule,
    state_paths: dict[str, Path],
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_events.return_value = event_schedule
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-events"],
    )

    assert result.exit_code == 0

    mocked_client.send_image.assert_called_once()
    mocked_client.send_animation.assert_not_called()

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == EVENT_PANEL_INDEX

    assert state_paths["events"].is_file()


@patch("novachrono.cli.widgets.fetch_event_artwork")
@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_events_skips_artwork_when_unchanged(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    event_schedule: EventSchedule,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_events.return_value = event_schedule
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-events"],
    )

    assert first_result.exit_code == 0

    mocked_fetch_artwork.reset_mock()
    mocked_client.send_image.reset_mock()
    mocked_client.send_animation.reset_mock()

    second_result = runner.invoke(
        app,
        ["send-events"],
    )

    assert second_result.exit_code == 0

    assert "Pokémon GO events unchanged; display update skipped." in second_result.stdout

    mocked_fetch_artwork.assert_not_called()
    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_not_called()


@patch("novachrono.cli.widgets.fetch_event_artwork")
@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_events_force_sends_unchanged_schedule(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    event_schedule: EventSchedule,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_events.return_value = event_schedule
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-events"],
    )

    forced_result = runner.invoke(
        app,
        [
            "send-events",
            "--force",
        ],
    )

    assert first_result.exit_code == 0
    assert forced_result.exit_code == 0

    assert mocked_fetch_artwork.call_count == 2
    assert mocked_client.send_image.call_count == 2


@patch("novachrono.cli.widgets.fetch_event_artwork")
@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_events_uses_animation_for_multiple_frames(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    multi_event_schedule: EventSchedule,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_events.return_value = multi_event_schedule
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_animation.return_value = (
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    )

    result = runner.invoke(
        app,
        ["send-events"],
    )

    assert result.exit_code == 0

    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == EVENT_PANEL_INDEX
    assert len(arguments["images"]) == 2
    assert arguments["frame_duration_ms"] == 30_000


@patch("novachrono.cli.widgets._load_event_schedule")
@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets.fetch_raid_artwork")
@patch("novachrono.cli.widgets.localize_raid_roster")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_raids_uses_static_image_for_single_frame(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_artwork: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    app_config: AppConfig,
    raid_roster: RaidRoster,
    state_paths: dict[str, Path],
) -> None:
    mocked_load_config.return_value = replace(
        app_config,
        weather=WeatherSettings(
            latitude=None,
            longitude=None,
        ),
    )

    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-raids"],
    )

    assert result.exit_code == 0

    mocked_load_weather.assert_not_called()
    mocked_load_events.assert_not_called()

    mocked_client.send_image.assert_called_once()
    mocked_client.send_animation.assert_not_called()

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == RAID_PANEL_INDEX

    assert state_paths["raids"].is_file()


@patch("novachrono.cli.widgets.fetch_raid_artwork")
@patch("novachrono.cli.widgets.localize_raid_roster")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_raids_skips_artwork_when_localized_roster_is_unchanged(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-raids"],
    )

    assert first_result.exit_code == 0

    mocked_localize_raids.reset_mock()
    mocked_fetch_artwork.reset_mock()
    mocked_client.send_image.reset_mock()
    mocked_client.send_animation.reset_mock()

    second_result = runner.invoke(
        app,
        ["send-raids"],
    )

    assert second_result.exit_code == 0

    assert "Pokémon GO raids unchanged; display update skipped." in second_result.stdout

    mocked_localize_raids.assert_called_once_with(
        raid_roster,
        locale=app_config.locale,
    )

    mocked_fetch_artwork.assert_not_called()
    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_not_called()


@patch("novachrono.cli.widgets.fetch_raid_artwork")
@patch("novachrono.cli.widgets.localize_raid_roster")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_raids_sends_when_localized_roster_changes(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    raid_roster: RaidRoster,
) -> None:
    assert raid_roster.five_star

    localized_roster = replace(
        raid_roster,
        five_star=(
            replace(
                raid_roster.five_star[0],
                name="Lokalisierter Boss",
            ),
        ),
    )

    mocked_load_config.return_value = app_config
    mocked_load_raids.return_value = raid_roster

    mocked_localize_raids.side_effect = (
        raid_roster,
        localized_roster,
    )

    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-raids"],
    )

    second_result = runner.invoke(
        app,
        ["send-raids"],
    )

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    assert mocked_localize_raids.call_count == 2
    assert mocked_fetch_artwork.call_count == 2
    assert mocked_client.send_image.call_count == 2


@patch("novachrono.cli.widgets.fetch_raid_artwork")
@patch("novachrono.cli.widgets.localize_raid_roster")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_raids_force_sends_unchanged_roster(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-raids"],
    )

    forced_result = runner.invoke(
        app,
        [
            "send-raids",
            "--force",
        ],
    )

    assert first_result.exit_code == 0
    assert forced_result.exit_code == 0

    assert mocked_localize_raids.call_count == 2
    assert mocked_fetch_artwork.call_count == 2
    assert mocked_client.send_image.call_count == 2


@patch("novachrono.cli.widgets.fetch_raid_artwork")
@patch("novachrono.cli.widgets.localize_raid_roster")
@patch("novachrono.cli.widgets._load_raw_raid_roster")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_raids_uses_animation_for_multiple_bosses(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_artwork: MagicMock,
    app_config: AppConfig,
    multi_raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_raids.return_value = multi_raid_roster
    mocked_localize_raids.return_value = multi_raid_roster
    mocked_fetch_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.send_animation.return_value = (
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    )

    result = runner.invoke(
        app,
        ["send-raids"],
    )

    assert result.exit_code == 0

    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == RAID_PANEL_INDEX
    assert len(arguments["images"]) == 2
    assert arguments["frame_duration_ms"] == 10_000


@patch("novachrono.cli._common.fetch_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_reports_open_meteo_error(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_fetch_weather: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = app_config

    mocked_fetch_weather.side_effect = OpenMeteoError("Weather service unavailable")

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 1
    assert "Weather service unavailable" in result.stderr

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.assert_not_called()


@patch("novachrono.cli._common.fetch_raid_roster")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_raids_reports_scraped_duck_error(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_fetch_raids: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = app_config

    mocked_fetch_raids.side_effect = ScrapedDuckError("Raid service unavailable")

    result = runner.invoke(
        app,
        ["send-raids"],
    )

    assert result.exit_code == 1
    assert "Raid service unavailable" in result.stderr

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.assert_not_called()


@patch("novachrono.cli._common.fetch_event_schedule")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_events_reports_scraped_duck_error(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_fetch_events: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = app_config

    mocked_fetch_events.side_effect = ScrapedDuckError("Event service unavailable")

    result = runner.invoke(
        app,
        ["send-events"],
    )

    assert result.exit_code == 1
    assert "Event service unavailable" in result.stderr

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.assert_not_called()


@patch("novachrono.outputs.delivery.sleep")
@patch("novachrono.cli.widgets._load_current_weather")
@patch("novachrono.cli.widgets._create_times_gate_client")
@patch("novachrono.cli.widgets._load_app_config")
def test_send_weather_reports_times_gate_error_after_retry(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_sleep: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    state_paths: dict[str, Path],
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather

    mocked_client = mocked_create_client.return_value
    mocked_client.send_image.side_effect = TimesGateError("Connection failed")

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 1
    assert "Connection failed" in result.stderr

    assert mocked_client.send_image.call_count == 2
    mocked_sleep.assert_called_once_with(5.0)

    assert not state_paths["weather"].exists()
