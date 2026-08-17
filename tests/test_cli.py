from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from PIL import Image
from typer.testing import CliRunner

from novachrono.cli import app
from novachrono.config import (
    AppConfig,
    TimesGateSettings,
    WeatherSettings,
)
from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    POKEMON_GO_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
)
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.outputs.times_gate import TimesGateError
from novachrono.pokemon_go import (
    CombatPowerRange,
    PokemonType,
    RaidBoss,
    RaidRoster,
    RaidTier,
)
from novachrono.sources.open_meteo import OpenMeteoError
from novachrono.sources.scraped_duck import ScrapedDuckError
from novachrono.units import TemperatureUnit
from novachrono.weather import CurrentWeather

runner = CliRunner()


@pytest.fixture
def multi_raid_roster(raid_roster: RaidRoster) -> RaidRoster:
    """Two five-star bosses to trigger animation rendering."""

    second_five_star = RaidBoss(
        name="Zamazenta",
        tier=RaidTier.FIVE_STAR,
        can_be_shiny=True,
        types=(PokemonType.FIGHTING,),
        normal_combat_power=CombatPowerRange(
            minimum=2100,
            maximum=2188,
        ),
        boosted_combat_power=CombatPowerRange(
            minimum=2625,
            maximum=2735,
        ),
    )

    return RaidRoster(
        five_star=(
            *raid_roster.five_star,
            second_five_star,
        ),
        mega=raid_roster.mega,
    )


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
    assert "send-pokemon" in result.stdout
    assert "send-dashboard" in result.stdout


@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.load_config")
def test_preview_command_creates_preview(
    mocked_load_config: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
    tmp_path: Path,
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = _create_app_config()
    mocked_load_weather.return_value = weather
    mocked_load_raids.return_value = raid_roster

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
@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.load_config")
def test_preview_passes_external_data_to_dashboard(
    mocked_load_config: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_render_dashboard: MagicMock,
    tmp_path: Path,
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    app_config = _create_app_config(
        locale="en_US",
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )

    mocked_load_config.return_value = app_config
    mocked_load_weather.return_value = weather
    mocked_load_raids.return_value = raid_roster

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
        raid_roster=raid_roster,
        raid_artwork={},
        timezone=app_config.timezone,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )


@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.load_config")
def test_check_device_uses_configured_connection(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
) -> None:
    mocked_load_config.return_value = _create_app_config()

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


@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.load_config")
def test_cli_options_override_configuration(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
) -> None:
    mocked_load_config.return_value = _create_app_config()

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


@patch("novachrono.cli.load_config")
def test_check_device_reports_missing_configuration(
    mocked_load_config: MagicMock,
) -> None:
    mocked_load_config.return_value = _create_app_config(
        host=None,
        local_token=None,
    )

    result = runner.invoke(
        app,
        ["check-device"],
    )

    assert result.exit_code == 1
    assert "NOVACHRONO_TIMES_GATE_HOST" in result.stderr
    assert "NOVACHRONO_TIMES_GATE_TOKEN" in result.stderr


@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.load_config")
def test_send_clock_fetches_no_external_data(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
) -> None:
    mocked_load_config.return_value = _create_app_config(
        weather_latitude=None,
        weather_longitude=None,
    )

    mocked_client = mocked_client_class.return_value
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

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == CLOCK_PANEL_INDEX


@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.load_config")
def test_send_weather_targets_weather_display_only(
    mocked_load_config: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_client_class: MagicMock,
    mocked_load_raids: MagicMock,
    weather: CurrentWeather,
) -> None:
    mocked_load_config.return_value = _create_app_config()
    mocked_load_weather.return_value = weather

    mocked_client = mocked_client_class.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 0

    mocked_load_raids.assert_not_called()

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == WEATHER_PANEL_INDEX


@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli.load_config")
def test_send_pokemon_uses_static_image_for_single_frame(
    mocked_load_config: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_client_class: MagicMock,
    mocked_load_weather: MagicMock,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = _create_app_config(
        weather_latitude=None,
        weather_longitude=None,
    )
    mocked_load_raids.return_value = raid_roster

    mocked_client = mocked_client_class.return_value
    mocked_client.send_image.return_value = {
        "ReturnCode": 0,
    }

    result = runner.invoke(
        app,
        ["send-pokemon"],
    )

    assert result.exit_code == 0

    mocked_load_weather.assert_not_called()
    mocked_client.send_image.assert_called_once()
    mocked_client.send_animation.assert_not_called()

    assert mocked_client.send_image.call_args.kwargs["panel_index"] == POKEMON_GO_PANEL_INDEX


@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli.load_config")
def test_send_pokemon_uses_animation_for_multiple_bosses(
    mocked_load_config: MagicMock,
    mocked_load_raids: MagicMock,
    mocked_client_class: MagicMock,
    mocked_load_weather: MagicMock,
    multi_raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = _create_app_config(
        weather_latitude=None,
        weather_longitude=None,
    )
    mocked_load_raids.return_value = multi_raid_roster

    mocked_client = mocked_client_class.return_value
    mocked_client.send_animation.return_value = (
        {"ReturnCode": 0},
        {"ReturnCode": 0},
    )

    result = runner.invoke(
        app,
        ["send-pokemon"],
    )

    assert result.exit_code == 0

    mocked_load_weather.assert_not_called()
    mocked_client.send_image.assert_not_called()
    mocked_client.send_animation.assert_called_once()

    arguments = mocked_client.send_animation.call_args.kwargs

    assert arguments["panel_index"] == POKEMON_GO_PANEL_INDEX
    assert len(arguments["images"]) == 2
    assert arguments["frame_duration_ms"] == 10_000


@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.fetch_current_weather")
@patch("novachrono.cli.load_config")
def test_send_weather_reports_open_meteo_error(
    mocked_load_config: MagicMock,
    mocked_fetch_weather: MagicMock,
    mocked_client_class: MagicMock,
) -> None:
    mocked_load_config.return_value = _create_app_config()

    mocked_fetch_weather.side_effect = OpenMeteoError("Weather service unavailable")

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 1
    assert "Weather service unavailable" in result.stderr


@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.fetch_raid_roster")
@patch("novachrono.cli.load_config")
def test_send_pokemon_reports_scraped_duck_error(
    mocked_load_config: MagicMock,
    mocked_fetch_raids: MagicMock,
    mocked_client_class: MagicMock,
) -> None:
    mocked_load_config.return_value = _create_app_config()

    mocked_fetch_raids.side_effect = ScrapedDuckError("Raid service unavailable")

    result = runner.invoke(
        app,
        ["send-pokemon"],
    )

    assert result.exit_code == 1
    assert "Raid service unavailable" in result.stderr


@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.load_config")
def test_send_weather_reports_times_gate_error(
    mocked_load_config: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_client_class: MagicMock,
    weather: CurrentWeather,
) -> None:
    mocked_load_config.return_value = _create_app_config()
    mocked_load_weather.return_value = weather

    mocked_client = mocked_client_class.return_value
    mocked_client.send_image.side_effect = TimesGateError("Connection failed")

    result = runner.invoke(
        app,
        ["send-weather"],
    )

    assert result.exit_code == 1
    assert "Connection failed" in result.stderr


@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.load_config")
def test_send_dashboard_uses_static_images_for_single_pokemon_frame(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = _create_app_config()
    mocked_load_weather.return_value = weather
    mocked_load_raids.return_value = raid_roster

    mocked_client = mocked_client_class.return_value
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


@patch("novachrono.cli._load_raid_roster")
@patch("novachrono.cli._load_current_weather")
@patch("novachrono.cli.TimesGateClient")
@patch("novachrono.cli.load_config")
def test_send_dashboard_uses_animation_for_pokemon_display(
    mocked_load_config: MagicMock,
    mocked_client_class: MagicMock,
    mocked_load_weather: MagicMock,
    mocked_load_raids: MagicMock,
    weather: CurrentWeather,
    multi_raid_roster: RaidRoster,
) -> None:
    mocked_load_config.return_value = _create_app_config()
    mocked_load_weather.return_value = weather
    mocked_load_raids.return_value = multi_raid_roster

    mocked_client = mocked_client_class.return_value
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

    assert arguments["panel_index"] == POKEMON_GO_PANEL_INDEX
    assert len(arguments["images"]) == 2
    assert arguments["frame_duration_ms"] == 10_000


def _create_app_config(
    *,
    host: str | None = "192.168.178.50",
    local_token: str | None = "secret",
    locale: str = "de_DE",
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
    weather_latitude: float | None = 53.04771,
    weather_longitude: float | None = 8.80169,
) -> AppConfig:
    return AppConfig(
        timezone=ZoneInfo("Europe/Berlin"),
        locale=locale,
        temperature_unit=temperature_unit,
        weather=WeatherSettings(
            latitude=weather_latitude,
            longitude=weather_longitude,
        ),
        times_gate=TimesGateSettings(
            host=host,
            local_token=local_token,
        ),
    )
