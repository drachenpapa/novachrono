import io
from collections.abc import Iterable
from typing import Final
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image

from novachrono.models.pokemon_go import (
    EventSchedule,
    RaidRoster,
)

DEFAULT_TIMEOUT_SECONDS: Final = 6.0


def fetch_raid_artwork(
    roster: RaidRoster,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Image.Image]:
    """Retrieve artwork for the raid bosses in a roster."""

    return _fetch_artwork_urls(_raid_artwork_urls(roster), timeout_seconds=timeout_seconds)


def fetch_event_artwork(
    schedule: EventSchedule,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Image.Image]:
    """Retrieve artwork for featured event Pokémon."""

    return _fetch_artwork_urls(_event_artwork_urls(schedule), timeout_seconds=timeout_seconds)


def _fetch_artwork_urls(
    artwork_urls: tuple[str, ...],
    *,
    timeout_seconds: float,
) -> dict[str, Image.Image]:
    if timeout_seconds <= 0:
        raise ValueError("Pokémon artwork timeout must be greater than zero")

    artwork_by_url: dict[str, Image.Image] = {}

    for artwork_url in artwork_urls:
        artwork = _fetch_artwork(artwork_url, timeout_seconds=(timeout_seconds))

        if artwork is not None:
            artwork_by_url[artwork_url] = artwork

    return artwork_by_url


def _raid_artwork_urls(roster: RaidRoster) -> tuple[str, ...]:
    return _unique_artwork_urls(
        boss.artwork_url
        for boss in (
            *roster.five_star,
            *roster.shadow_five_star,
            *roster.mega,
        )
    )


def _event_artwork_urls(schedule: EventSchedule) -> tuple[str, ...]:
    events = (
        schedule.community_day,
        schedule.community_day_classic,
        schedule.spotlight_hour,
        schedule.max_monday,
    )

    return _unique_artwork_urls(
        pokemon.artwork_url
        for event in events
        if event is not None
        for pokemon in (event.featured_pokemon)
    )


def _unique_artwork_urls(artwork_urls: Iterable[str | None]) -> tuple[str, ...]:
    unique_urls: list[str] = []
    seen_urls: set[str] = set()

    for artwork_url in artwork_urls:
        if artwork_url is None or artwork_url in seen_urls:
            continue

        seen_urls.add(artwork_url)
        unique_urls.append(artwork_url)

    return tuple(unique_urls)


def _fetch_artwork(
    artwork_url: str,
    *,
    timeout_seconds: float,
) -> Image.Image | None:
    if not _is_https_url(artwork_url):
        return None

    request = Request(
        url=artwork_url,
        headers={
            "Accept": "image/*",
            "User-Agent": "Novachrono",
        },
        method="GET",
    )

    try:
        with urlopen(  # nosec B310 - validated HTTPS artwork URL
            request,
            timeout=timeout_seconds,
        ) as response:
            image_data = response.read()
    except URLError, TimeoutError:
        return None

    try:
        with Image.open(io.BytesIO(image_data)) as downloaded_image:
            artwork = downloaded_image.convert("RGBA")
    except OSError:
        return None

    return _trim_transparent_border(artwork)


def _is_https_url(value: str) -> bool:
    parsed_url = urlparse(value)

    return parsed_url.scheme.casefold() == "https" and parsed_url.hostname is not None


def _trim_transparent_border(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bounding_box = alpha.getbbox()

    if bounding_box is None:
        return image

    return image.crop(bounding_box)
