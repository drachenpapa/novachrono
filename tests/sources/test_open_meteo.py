import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import pytest

from novachrono.sources.open_meteo import (
    DEFAULT_TIMEOUT_SECONDS,
    OpenMeteoError,
    fetch_current_weather,
    map_weather_code,
)
from novachrono.weather import CurrentWeather, WeatherCondition

BERLIN = ZoneInfo("Europe/Berlin")

LATITUDE = 53.04771
LONGITUDE = 8.80169


def _create_response(payload: object) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def _create_raw_response(body: str) -> MagicMock:
    response = MagicMock()
    response.read.return_value = body.encode("utf-8")

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    return context_manager


def _create_weather_response(
    *,
    weather_code: int = 2,
    is_day: int = 1,
    temperature: float = 22.6,
    high_temperature: float = 26.4,
    low_temperature: float = 14.6,
    precipitation_probability: float = 34.6,
) -> dict[str, object]:
    return {
        "current": {
            "temperature_2m": temperature,
            "weather_code": weather_code,
            "is_day": is_day,
        },
        "daily": {
            "temperature_2m_max": [high_temperature],
            "temperature_2m_min": [low_temperature],
            "precipitation_probability_max": [precipitation_probability],
        },
    }


@pytest.mark.parametrize(
    ("weather_code", "expected_condition"),
    [
        (0, WeatherCondition.CLEAR),
        (1, WeatherCondition.CLEAR),
        (2, WeatherCondition.PARTLY_CLOUDY),
        (3, WeatherCondition.CLOUDY),
        (45, WeatherCondition.FOG),
        (48, WeatherCondition.FOG),
        (51, WeatherCondition.RAIN),
        (53, WeatherCondition.RAIN),
        (55, WeatherCondition.RAIN),
        (56, WeatherCondition.RAIN),
        (57, WeatherCondition.RAIN),
        (61, WeatherCondition.RAIN),
        (63, WeatherCondition.RAIN),
        (65, WeatherCondition.RAIN),
        (66, WeatherCondition.RAIN),
        (67, WeatherCondition.RAIN),
        (80, WeatherCondition.RAIN),
        (81, WeatherCondition.RAIN),
        (82, WeatherCondition.RAIN),
        (71, WeatherCondition.SNOW),
        (73, WeatherCondition.SNOW),
        (75, WeatherCondition.SNOW),
        (77, WeatherCondition.SNOW),
        (85, WeatherCondition.SNOW),
        (86, WeatherCondition.SNOW),
        (95, WeatherCondition.THUNDERSTORM),
        (96, WeatherCondition.THUNDERSTORM),
        (99, WeatherCondition.THUNDERSTORM),
    ],
)
def test_map_weather_code(
    weather_code: int,
    expected_condition: WeatherCondition,
) -> None:
    assert map_weather_code(weather_code) is expected_condition


def test_map_weather_code_rejects_unknown_code() -> None:
    with pytest.raises(
        OpenMeteoError,
        match="Unsupported Open-Meteo weather code",
    ):
        map_weather_code(999)


@patch("novachrono.sources.open_meteo.urlopen")
def test_fetch_current_weather_returns_normalized_weather(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(_create_weather_response())

    weather = fetch_current_weather(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        timezone=BERLIN,
    )

    assert weather == CurrentWeather(
        condition=WeatherCondition.PARTLY_CLOUDY,
        temperature=23,
        high_temperature=26,
        low_temperature=15,
        precipitation_probability=35,
        is_day=True,
    )


@patch("novachrono.sources.open_meteo.urlopen")
def test_fetch_current_weather_sends_expected_request(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(_create_weather_response())

    fetch_current_weather(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        timezone=BERLIN,
    )

    request = mocked_urlopen.call_args.args[0]
    query = parse_qs(urlparse(request.full_url).query)

    assert request.full_url.startswith("https://api.open-meteo.com/v1/forecast?")
    assert query["latitude"] == ["53.04771"]
    assert query["longitude"] == ["8.80169"]
    assert query["current"] == ["temperature_2m,weather_code,is_day"]
    assert query["daily"] == ["temperature_2m_max,temperature_2m_min,precipitation_probability_max"]
    assert query["temperature_unit"] == ["celsius"]
    assert query["timezone"] == ["Europe/Berlin"]
    assert query["forecast_days"] == ["1"]
    assert mocked_urlopen.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS


@patch("novachrono.sources.open_meteo.urlopen")
def test_fetch_current_weather_supports_night(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        _create_weather_response(
            weather_code=0,
            is_day=0,
        )
    )

    weather = fetch_current_weather(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        timezone=BERLIN,
    )

    assert weather.condition is WeatherCondition.CLEAR
    assert weather.is_day is False


def test_fetch_current_weather_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
            timeout_seconds=0,
        )


@patch("novachrono.sources.open_meteo.urlopen")
def test_connection_error_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = URLError("Connection refused")

    with pytest.raises(
        OpenMeteoError,
        match="Could not reach Open-Meteo",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@patch("novachrono.sources.open_meteo.urlopen")
def test_timeout_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.side_effect = TimeoutError()

    with pytest.raises(
        OpenMeteoError,
        match="timed out",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@patch("novachrono.sources.open_meteo.urlopen")
def test_http_error_uses_open_meteo_reason(
    mocked_urlopen: MagicMock,
) -> None:
    error_body = json.dumps({"reason": "Invalid latitude"}).encode("utf-8")

    mocked_urlopen.side_effect = HTTPError(
        url="https://api.open-meteo.com/v1/forecast",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=io.BytesIO(error_body),
    )

    with pytest.raises(
        OpenMeteoError,
        match="Invalid latitude",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@patch("novachrono.sources.open_meteo.urlopen")
def test_invalid_json_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_raw_response("definitely not json")

    with pytest.raises(
        OpenMeteoError,
        match="invalid JSON",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@patch("novachrono.sources.open_meteo.urlopen")
def test_unexpected_json_structure_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        [
            {
                "current": {},
            }
        ]
    )

    with pytest.raises(
        OpenMeteoError,
        match="unexpected response",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@pytest.mark.parametrize("missing_section", ["current", "daily"])
@patch("novachrono.sources.open_meteo.urlopen")
def test_missing_response_section_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
    missing_section: str,
) -> None:
    response = _create_weather_response()
    del response[missing_section]

    mocked_urlopen.return_value = _create_response(response)

    with pytest.raises(
        OpenMeteoError,
        match=f"missing '{missing_section}'",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@patch("novachrono.sources.open_meteo.urlopen")
def test_invalid_precipitation_probability_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
) -> None:
    mocked_urlopen.return_value = _create_response(
        _create_weather_response(
            precipitation_probability=101,
        )
    )

    with pytest.raises(
        OpenMeteoError,
        match="invalid precipitation probability",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )


@pytest.mark.parametrize("is_day", [-1, 2])
@patch("novachrono.sources.open_meteo.urlopen")
def test_invalid_is_day_raises_open_meteo_error(
    mocked_urlopen: MagicMock,
    is_day: int,
) -> None:
    mocked_urlopen.return_value = _create_response(_create_weather_response(is_day=is_day))

    with pytest.raises(
        OpenMeteoError,
        match="invalid is_day",
    ):
        fetch_current_weather(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            timezone=BERLIN,
        )
