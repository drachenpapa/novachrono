import json
import os
from contextlib import suppress
from hashlib import sha256
from pathlib import Path
from typing import Final

from novachrono.models.pokemon_go import RaidBoss, RaidRoster
from novachrono.models.weather import CurrentWeather
from novachrono.units import TemperatureUnit

STATE_DIRECTORY: Final = Path.home() / ".novachrono"
WEATHER_STATE_PATH: Final = STATE_DIRECTORY / "weather.state"
POKEMON_GO_STATE_PATH: Final = STATE_DIRECTORY / "pokemon-go.state"

FINGERPRINT_VERSION: Final = 1
_HEX_CHARACTERS: Final = frozenset("0123456789abcdefABCDEF")


class StateError(RuntimeError):
    """Raised when persistent Novachrono state cannot be accessed."""


def weather_fingerprint(
    weather: CurrentWeather,
    *,
    locale: str,
    temperature_unit: TemperatureUnit,
) -> str:
    """Create a fingerprint for rendering-relevant weather state."""

    return _fingerprint(
        {
            "version": FINGERPRINT_VERSION,
            "locale": locale,
            "temperature_unit": temperature_unit.value,
            "condition": weather.condition.value,
            "temperature": weather.temperature,
            "high_temperature": weather.high_temperature,
            "low_temperature": weather.low_temperature,
            "precipitation_probability": weather.precipitation_probability,
            "is_day": weather.is_day,
        }
    )


def raid_roster_fingerprint(
    roster: RaidRoster,
    *,
    locale: str,
) -> str:
    """Create a fingerprint for rendering-relevant raid state."""

    return _fingerprint(
        {
            "version": FINGERPRINT_VERSION,
            "locale": locale,
            "five_star": [_raid_boss_payload(boss) for boss in roster.five_star],
            "shadow_five_star": [_raid_boss_payload(boss) for boss in roster.shadow_five_star],
            "mega": [_raid_boss_payload(boss) for boss in roster.mega],
        }
    )


def read_fingerprint(path: Path) -> str | None:
    """Read a stored fingerprint.

    Missing or malformed state is treated as a cache miss.
    """

    try:
        value = path.read_text(
            encoding="ascii",
        ).strip()
    except FileNotFoundError:
        return None
    except UnicodeError:
        return None
    except OSError as error:
        raise StateError(f"Could not read state file {path}: {error}") from error

    if not _is_valid_fingerprint(value):
        return None

    return value.lower()


def write_fingerprint(
    path: Path,
    fingerprint: str,
) -> None:
    """Persist a fingerprint atomically."""

    if not _is_valid_fingerprint(fingerprint):
        raise ValueError("State fingerprint must be a SHA-256 hexadecimal digest")

    temporary_path = path.with_name(
        f".{path.name}.{os.getpid()}.tmp",
    )

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path.write_text(f"{fingerprint.lower()}\n", encoding="ascii")

        temporary_path.replace(path)
    except OSError as error:
        with suppress(OSError):
            temporary_path.unlink(missing_ok=True)

        raise StateError(f"Could not write state file {path}: {error}") from error


def _fingerprint(payload: object) -> str:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return sha256(serialized.encode("utf-8")).hexdigest()


def _raid_boss_payload(boss: RaidBoss) -> dict[str, str | bool | None]:
    return {
        "name": boss.name,
        "can_be_shiny": boss.can_be_shiny,
        "artwork_url": boss.artwork_url,
    }


def _is_valid_fingerprint(value: str) -> bool:
    return len(value) == 64 and all(character in _HEX_CHARACTERS for character in value)
