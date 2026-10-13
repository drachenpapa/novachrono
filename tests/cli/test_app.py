from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
from typer.testing import CliRunner

from novachrono.cli import app
from novachrono.config import AppConfig, TimesGateSettings
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.models.pokemon_go import EventSchedule, RaidRoster
from novachrono.models.weather import CurrentWeather
from novachrono.units import TemperatureUnit

runner = CliRunner()


def test_help_lists_available_commands() -> None:
    result = runner.invoke(
        app,
        ["--help"],
    )

    assert result.exit_code == 0
    assert "preview" in result.stdout
    assert "check-device" in result.stdout
    assert "send-clock" in result.stdout
    assert "send-weather" in result.stdout
    assert "send-raids" in result.stdout
    assert "send-events" in result.stdout
    assert "send-dashboard" in result.stdout

    assert "send-pokemon" not in result.stdout
    assert "update-weather" not in result.stdout
    assert "update-pokemon" not in result.stdout
    assert "run" not in result.stdout


@patch("novachrono.cli.fetch_raid_artwork")
@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli.fetch_event_artwork")
@patch("novachrono.cli._load_event_schedule")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli._load_app_config")
def test_preview_command_creates_preview(
    mocked_load_config: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    tmp_path: Path,
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
    mocked_fetch_raid_artwork.return_value = {}

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


@patch("novachrono.cli.render_dashboard")
@patch("novachrono.cli.fetch_raid_artwork")
@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli.fetch_event_artwork")
@patch("novachrono.cli._load_event_schedule")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli._load_app_config")
def test_preview_passes_external_data_to_dashboard(
    mocked_load_config: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_events: MagicMock,
    mocked_fetch_event_artwork: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_fetch_raid_artwork: MagicMock,
    mocked_render_dashboard: MagicMock,
    tmp_path: Path,
    app_config: AppConfig,
    weather: CurrentWeather,
    event_schedule: EventSchedule,
    raid_roster: RaidRoster,
) -> None:
    configured_app = replace(
        app_config,
        locale="en_US",
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )

    event_artwork: dict[str, Image.Image] = {}
    raid_artwork: dict[str, Image.Image] = {}

    mocked_load_config.return_value = configured_app
    mocked_load_weather.return_value = weather
    mocked_load_events.return_value = event_schedule
    mocked_fetch_event_artwork.return_value = event_artwork
    mocked_load_raids.return_value = raid_roster
    mocked_fetch_raid_artwork.return_value = raid_artwork

    mocked_render_dashboard.return_value = tuple(
        Image.new(
            mode="RGB",
            size=(PANEL_SIZE, PANEL_SIZE),
        )
        for _ in range(PANEL_COUNT)
    )

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

    mocked_render_dashboard.assert_called_once_with(
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        event_artwork=event_artwork,
        raid_artwork=raid_artwork,
        timezone=configured_app.timezone,
        locale=configured_app.locale,
        temperature_unit=configured_app.temperature_unit,
    )


@patch("novachrono.cli._common.TimesGateClient")
@patch("novachrono.cli._load_app_config")
def test_check_device_uses_configured_connection(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = app_config

    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://192.168.178.50:9000/divoom_api"
    mocked_client.get_configuration.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["check-device"],
    )

    assert result.exit_code == 0

    config = mocked_client_class.call_args.args[0]

    assert config.host == "192.168.178.50"
    assert config.local_token == "secret"


@patch("novachrono.cli._common.TimesGateClient")
@patch("novachrono.cli._load_app_config")
def test_cli_options_override_configuration(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = app_config

    mocked_client = mocked_client_class.return_value
    mocked_client.config.api_url = "http://10.0.0.50:9000/divoom_api"
    mocked_client.get_configuration.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        [
            "check-device",
            "--host",
            "10.0.0.50",
            "--token",
            "override-token",
        ],
    )

    assert result.exit_code == 0

    config = mocked_client_class.call_args.args[0]

    assert config.host == "10.0.0.50"
    assert config.local_token == "override-token"


@patch("novachrono.cli._load_app_config")
def test_check_device_reports_missing_configuration(
    mocked_load_config: MagicMock,
    app_config: AppConfig,
) -> None:
    mocked_load_config.return_value = replace(
        app_config,
        times_gate=TimesGateSettings(
            host=None,
            local_token=None,
        ),
    )

    result = runner.invoke(
        app,
        ["check-device"],
    )

    assert result.exit_code == 1
    assert "NOVACHRONO_TIMES_GATE_HOST" in result.stderr
    assert "NOVACHRONO_TIMES_GATE_TOKEN" in result.stderr
