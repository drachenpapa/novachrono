import json
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS: Final = 8.0


class ScrapedDuckError(RuntimeError):
    """Raised when ScrapedDuck Pokémon GO data cannot be retrieved."""


def _fetch_entries(
    url: str,
    *,
    timeout_seconds: float,
) -> list[Any]:
    request = Request(url=url, headers={"Accept": "application/json"}, method="GET")

    try:
        with urlopen(  # nosec B310 - fixed ScrapedDuck HTTPS endpoints
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise ScrapedDuckError(f"ScrapedDuck returned HTTP {error.code}: {error.reason}") from error
    except URLError as error:
        raise ScrapedDuckError(f"Could not reach ScrapedDuck: {error.reason}") from error
    except TimeoutError as error:
        raise ScrapedDuckError("Connection to ScrapedDuck timed out") from error
    except UnicodeDecodeError as error:
        raise ScrapedDuckError("ScrapedDuck returned an invalid UTF-8 response") from error

    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise ScrapedDuckError("ScrapedDuck returned invalid JSON") from error

    if not isinstance(response_data, list):
        raise ScrapedDuckError("ScrapedDuck returned an unexpected response")

    return response_data


def _validate_timeout(timeout_seconds: float) -> None:
    if timeout_seconds <= 0:
        raise ValueError("ScrapedDuck timeout must be greater than zero")


def _read_string(
    data: dict[str, Any],
    name: str,
) -> str:
    value = data.get(name)

    if not isinstance(value, str) or not value.strip():
        raise ScrapedDuckError(f"ScrapedDuck data contains invalid '{name}'")

    return value.strip()


def _read_optional_image_url(
    data: dict[str, Any],
    name: str,
) -> str | None:
    value = data.get(name)

    if not isinstance(value, str):
        return None

    normalized_value = value.strip()
    parsed_url = urlparse(normalized_value)

    if parsed_url.scheme.casefold() != "https" or parsed_url.hostname is None:
        return None

    return normalized_value
