import json
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS: Final = 8.0
_REGIONAL_FORMS: Final = {
    "alolan": ("alola", "Alola"),
    "galarian": ("galar", "Galar"),
    "hisuian": ("hisui", "Hisui"),
    "paldean": ("paldea", "Paldea"),
}


class PokeApiError(RuntimeError):
    """Raised when Pokémon data cannot be retrieved from PokeAPI."""


def _fetch_json(
    url: str,
    *,
    timeout_seconds: float,
) -> Any:
    request = Request(
        url=url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Novachrono",
        },
        method="GET",
    )

    try:
        with urlopen(  # nosec B310 - fixed PokeAPI HTTPS endpoints
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise PokeApiError(f"PokeAPI returned HTTP {error.code}: {error.reason}") from error
    except URLError as error:
        raise PokeApiError(f"Could not reach PokeAPI: {error.reason}") from error
    except TimeoutError as error:
        raise PokeApiError("Connection to PokeAPI timed out") from error
    except UnicodeDecodeError as error:
        raise PokeApiError("PokeAPI returned an invalid UTF-8 response") from error

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as error:
        raise PokeApiError("PokeAPI returned invalid JSON") from error


def _validate_timeout(timeout_seconds: float) -> None:
    if timeout_seconds <= 0:
        raise ValueError("PokeAPI timeout must be greater than zero")


def _parse_display_name(name: str) -> tuple[str, bool, str | None, str | None]:
    normalized_name = name.strip()
    is_mega = normalized_name.casefold().startswith(("mega ", "mega-"))
    mega_form: str | None = None
    regional_form: str | None = None

    if is_mega:
        normalized_name = normalized_name[5:].strip()

    if is_mega and normalized_name.endswith((" X", " Y", " Z")):
        mega_form = normalized_name[-1]
        normalized_name = normalized_name[:-2].strip()

    for form_name in _REGIONAL_FORMS:
        prefix = f"{form_name} "

        if normalized_name.casefold().startswith(prefix):
            regional_form = form_name
            normalized_name = normalized_name[len(prefix) :].strip()

            break

    if regional_form is None and normalized_name.endswith(")") and "(" in normalized_name:
        open_parenthesis = normalized_name.rfind("(")
        possible_form = normalized_name[open_parenthesis + 1 : -1].strip().casefold()

        if possible_form in _REGIONAL_FORMS:
            regional_form = possible_form
            normalized_name = normalized_name[:open_parenthesis].strip()

    if "(" in normalized_name:
        normalized_name = normalized_name.split("(", maxsplit=1)[0].strip()

    return (normalized_name, is_mega, mega_form, regional_form)


def _species_identifier(name: str) -> str:
    return name.casefold().replace("'", "").replace("\u2019", "").replace(".", "").replace(" ", "-")
