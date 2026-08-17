from dataclasses import dataclass
from enum import StrEnum


class WeatherCondition(StrEnum):
    """Weather conditions supported by Novachrono."""

    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    FOG = "fog"
    RAIN = "rain"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"


@dataclass(frozen=True)
class CurrentWeather:
    """Normalized current weather data."""

    condition: WeatherCondition
    temperature: int
    high_temperature: int
    low_temperature: int
    precipitation_probability: int
    is_day: bool = True
