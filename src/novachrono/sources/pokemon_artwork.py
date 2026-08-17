import io
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image

from novachrono.pokemon_go import RaidRoster

DEFAULT_TIMEOUT_SECONDS = 6.0


def fetch_raid_artwork(
    roster: RaidRoster,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Image.Image]:
    """Retrieve artwork for the raid bosses in a roster."""

    if timeout_seconds <= 0:
        raise ValueError("Pokémon artwork timeout must be greater than zero")

    artwork_by_url: dict[str, Image.Image] = {}

    for artwork_url in _artwork_urls(roster):
        artwork = _fetch_artwork(
            artwork_url,
            timeout_seconds=timeout_seconds,
        )

        if artwork is not None:
            artwork_by_url[artwork_url] = artwork

    return artwork_by_url


def _artwork_urls(roster: RaidRoster) -> tuple[str, ...]:
    artwork_urls: list[str] = []
    seen_urls: set[str] = set()

    for boss in (*roster.five_star, *roster.mega):
        artwork_url = boss.artwork_url

        if artwork_url is None or artwork_url in seen_urls:
            continue

        seen_urls.add(artwork_url)
        artwork_urls.append(artwork_url)

    return tuple(artwork_urls)


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
    except (HTTPError, URLError, TimeoutError):
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
