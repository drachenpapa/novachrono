from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from novachrono.cli import app
from novachrono.config import AppConfig
from novachrono.dashboard import (
    EVENT_PANEL_INDEX,
    RAID_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
)
from novachrono.design import PANEL_COUNT
from novachrono.display_state import (
    raid_roster_fingerprint,
    read_fingerprint,
)
from novachrono.models.pokemon_go import EventSchedule, RaidRoster
from novachrono.models.weather import CurrentWeather, WeatherCondition
from novachrono.outputs.times_gate import TimesGateError

runner = CliRunner()


@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_uses_static_images_for_single_frames(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
    state_paths: dict[str, Path],
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 0

    assert mocked_client.send_image.call_count == PANEL_COUNT
    mocked_client.send_animation.assert_not_called()

    panel_indices = [call.kwargs["panel_index"] for call in mocked_client.send_image.call_args_list]

    assert panel_indices == list(range(PANEL_COUNT))

    assert state_paths["events"].is_file()
    assert state_paths["weather"].is_file()
    assert state_paths["raids"].is_file()


@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_always_sends_even_when_state_exists(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    first_result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    second_result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    assert mocked_client.send_image.call_count == PANEL_COUNT * 2


@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_uses_animation_for_raid_display(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    multi_raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = multi_raid_roster
    mocked_localize_raids.return_value = multi_raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"

    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    mocked_client.send_animation.return_value = (
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    )

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 0

    assert mocked_client.send_image.call_count == PANEL_COUNT - 1

    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == RAID_PANEL_INDEX
    assert len(arguments["images"]) == 2
    assert arguments["frame_duration_ms"] == 10_000


@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_uses_animation_for_weather_display(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
) -> None:
    rainy_weather = replace(
        weather,
        condition=WeatherCondition.RAIN,
    )

    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = rainy_weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"

    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    mocked_client.send_animation.return_value = (
        {"ReturnCode": 0},
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    )

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 0

    assert mocked_client.send_image.call_count == PANEL_COUNT - 1

    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == WEATHER_PANEL_INDEX
    assert len(arguments["images"]) == 3
    assert arguments["frame_duration_ms"] == 350


@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_uses_animation_for_event_display(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    multi_event_schedule: EventSchedule,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = multi_event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"

    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    mocked_client.send_animation.return_value = (
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    )

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 0

    assert mocked_client.send_image.call_count == PANEL_COUNT - 1

    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == EVENT_PANEL_INDEX
    assert len(arguments["images"]) == 2
    assert arguments["frame_duration_ms"] == 30_000


@patch("novachrono.outputs.delivery.sleep")
@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_continues_after_display_failure(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    mocked_sleep: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"

    mocked_client.send_image.side_effect = [
        TimesGateError("Display unavailable"),
        TimesGateError("Display unavailable"),
        {"ReturnCode": 0},
        {"ReturnCode": 0},
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    ]

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 1

    assert mocked_client.send_image.call_count == PANEL_COUNT + 1

    mocked_client.send_animation.assert_not_called()
    mocked_sleep.assert_called_once_with(5.0)

    assert "Display 1 failed" in result.stderr

    assert "Dashboard delivery failed for display(s): 1" in result.stderr


@patch("novachrono.outputs.delivery.sleep")
@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_failed_weather_dashboard_delivery_does_not_update_weather_state(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    mocked_sleep: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
    state_paths: dict[str, Path],
) -> None:
    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"

    mocked_client.send_image.side_effect = [
        {"ReturnCode": 0},
        TimesGateError("Weather display unavailable"),
        TimesGateError("Weather display unavailable"),
        {"ReturnCode": 0},
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    ]

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 1

    assert not state_paths["weather"].exists()
    assert state_paths["raids"].is_file()
    assert state_paths["events"].is_file()

    mocked_sleep.assert_called_once_with(5.0)


@patch("novachrono.cli.dashboard.fetch_raid_artwork")
@patch("novachrono.cli.dashboard.localize_raid_roster")
@patch("novachrono.cli.dashboard._load_raw_raid_roster")
@patch("novachrono.cli.dashboard.fetch_event_artwork")
@patch("novachrono.cli.dashboard._load_event_schedule")
@patch("novachrono.cli.dashboard._load_current_weather")
@patch("novachrono.cli.dashboard._create_times_gate_client")
@patch("novachrono.cli.dashboard._load_app_config")
def test_send_dashboard_stores_localized_raid_fingerprint(
    mocked_load_config: MagicMock,
    mocked_create_client: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_localize_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
    state_paths: dict[str, Path],
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
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = {}
    mocked_load_raids.return_value = raid_roster
    mocked_localize_raids.return_value = localized_roster
    mocked_fetch_raid_artwork.return_value = {}

    mocked_client = mocked_create_client.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-dashboard"],
    )

    assert result.exit_code == 0

    expected_fingerprint = raid_roster_fingerprint(
        localized_roster,
        locale=app_config.locale,
    )

    assert read_fingerprint(state_paths["raids"]) == expected_fingerprint
