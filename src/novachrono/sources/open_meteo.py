import json
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from novachrono.weather import CurrentWeather, WeatherCondition

OPEN_METEO_API_URL: Final = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SECONDS: Final = 8.0

CURRENT_VARIABLES: Final = (
    "temperature_2m",
    "weather_code",
    "is_day",
)

DAILY_VARIABLES: Final = (
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
)


class OpenMeteoError(RuntimeError):
    """Raised when weather data cannot be retrieved from Open-Meteo."""


def fetch_current_weather(
    *,
    latitude: float,
    longitude: float,
    timezone: ZoneInfo,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> CurrentWeather:
    """Retrieve and normalize the current weather from Open-Meteo."""

    if timeout_seconds <= 0:
        raise ValueError("Open-Meteo timeout must be greater than zero")

    request = Request(
        url=_build_request_url(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        ),
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urlopen(  # nosec B310 - fixed Open-Meteo HTTPS endpoint
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise OpenMeteoError(_format_http_error(error)) from error
    except URLError as error:
        raise OpenMeteoError(f"Could not reach Open-Meteo: {error.reason}") from error
    except TimeoutError as error:
        raise OpenMeteoError("Connection to Open-Meteo timed out") from error
    except UnicodeDecodeError as error:
        raise OpenMeteoError("Open-Meteo returned an invalid UTF-8 response") from error

    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise OpenMeteoError("Open-Meteo returned invalid JSON") from error

    if not isinstance(response_data, dict):
        raise OpenMeteoError("Open-Meteo returned an unexpected response")

    return _parse_weather_response(response_data)


def map_weather_code(
    weather_code: int,
) -> WeatherCondition:
    """Map an Open-Meteo WMO weather code to a Novachrono condition."""

    if weather_code in {0, 1}:
        return WeatherCondition.CLEAR

    if weather_code == 2:
        return WeatherCondition.PARTLY_CLOUDY

    if weather_code == 3:
        return WeatherCondition.CLOUDY

    if weather_code in {45, 48}:
        return WeatherCondition.FOG

    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return WeatherCondition.RAIN

    if weather_code in {71, 73, 75, 77, 85, 86}:
        return WeatherCondition.SNOW

    if weather_code in {95, 96, 99}:
        return WeatherCondition.THUNDERSTORM

    raise OpenMeteoError(f"Unsupported Open-Meteo weather code: {weather_code}")


def _build_request_url(
    *,
    latitude: float,
    longitude: float,
    timezone: ZoneInfo,
) -> str:
    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(CURRENT_VARIABLES),
        "daily": ",".join(DAILY_VARIABLES),
        "temperature_unit": "celsius",
        "timezone": timezone.key,
        "forecast_days": 1,
    }

    return f"{OPEN_METEO_API_URL}?{urlencode(parameters)}"


def _parse_weather_response(
    response_data: dict[str, Any],
) -> CurrentWeather:
    current = _read_mapping(
        response_data,
        "current",
    )
    daily = _read_mapping(
        response_data,
        "daily",
    )

    weather_code = _read_integer(
        current,
        "weather_code",
    )

    temperature = round(
        _read_number(
            current,
            "temperature_2m",
        )
    )

    high_temperature = round(
        _read_daily_number(
            daily,
            "temperature_2m_max",
        )
    )

    low_temperature = round(
        _read_daily_number(
            daily,
            "temperature_2m_min",
        )
    )

    precipitation_probability = round(
        _read_daily_number(
            daily,
            "precipitation_probability_max",
        )
    )

    if not 0 <= precipitation_probability <= 100:
        raise OpenMeteoError("Open-Meteo returned an invalid precipitation probability")

    is_day_value = _read_integer(
        current,
        "is_day",
    )

    if is_day_value not in {0, 1}:
        raise OpenMeteoError("Open-Meteo returned an invalid is_day value")

    return CurrentWeather(
        condition=map_weather_code(weather_code),
        temperature=temperature,
        high_temperature=high_temperature,
        low_temperature=low_temperature,
        precipitation_probability=precipitation_probability,
        is_day=is_day_value == 1,
    )


def _read_mapping(
    data: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    value = data.get(name)

    if not isinstance(value, dict):
        raise OpenMeteoError(f"Open-Meteo response is missing '{name}'")

    return value


def _read_number(
    data: dict[str, Any],
    name: str,
) -> float:
    value = data.get(name)

    if isinstance(value, bool) or not isinstance(value, int | float):
        raise OpenMeteoError(f"Open-Meteo response contains invalid '{name}'")

    return float(value)


def _read_integer(
    data: dict[str, Any],
    name: str,
) -> int:
    value = _read_number(
        data,
        name,
    )

    if not value.is_integer():
        raise OpenMeteoError(f"Open-Meteo response contains invalid '{name}'")

    return int(value)


def _read_daily_number(
    data: dict[str, Any],
    name: str,
) -> float:
    value = data.get(name)

    if not isinstance(value, list) or not value:
        raise OpenMeteoError(f"Open-Meteo response contains invalid '{name}'")

    first_value = value[0]

    if isinstance(first_value, bool) or not isinstance(first_value, int | float):
        raise OpenMeteoError(f"Open-Meteo response contains invalid '{name}'")

    return float(first_value)


def _format_http_error(
    error: HTTPError,
) -> str:
    try:
        response_body = error.read().decode("utf-8")
        response_data = json.loads(response_body)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        response_data = None

    if isinstance(response_data, dict):
        reason = response_data.get("reason")

        if isinstance(reason, str) and reason:
            return f"Open-Meteo returned HTTP {error.code}: {reason}"

    return f"Open-Meteo returned HTTP {error.code}: {error.reason}"
