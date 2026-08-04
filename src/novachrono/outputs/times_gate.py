import base64
import io
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image

from novachrono.design import PANEL_COUNT, PANEL_SIZE

DEFAULT_API_PORT = 9000
DEFAULT_API_PATH = "/divoom_api"
DEFAULT_TIMEOUT_SECONDS = 8.0


class TimesGateError(RuntimeError):
    """Raised when communication with the Times Gate fails."""


@dataclass(frozen=True)
class TimesGateConfig:
    """Connection settings for a Times Gate."""

    host: str
    local_token: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        normalized_host = self.host.strip()

        if not normalized_host:
            raise ValueError("Times Gate host must not be empty")

        if normalized_host.startswith(("http://", "https://")):
            raise ValueError("Times Gate host must contain only the hostname or IP address")

        if not self.local_token.strip():
            raise ValueError("Times Gate local token must not be empty")

        if self.timeout_seconds <= 0:
            raise ValueError("Times Gate timeout must be greater than zero")

        object.__setattr__(self, "host", normalized_host)
        object.__setattr__(self, "local_token", self.local_token.strip())

    @property
    def api_url(self) -> str:
        """Return the local Times Gate API URL."""

        return f"http://{self.host}:{DEFAULT_API_PORT}{DEFAULT_API_PATH}"


class TimesGateClient:
    """Communicate with a Divoom Times Gate over the local network."""

    def __init__(self, config: TimesGateConfig) -> None:
        self._config = config
        self._next_picture_id = int(time.time())

    @property
    def config(self) -> TimesGateConfig:
        """Return the client configuration."""

        return self._config

    def get_configuration(self) -> dict[str, Any]:
        """Retrieve the current Times Gate configuration."""

        return self._post(
            {
                "Command": "Channel/GetAllConf",
                "LocalToken": self._config.local_token,
            }
        )

    def send_image(
        self,
        panel_index: int,
        image: Image.Image,
    ) -> dict[str, Any]:
        """Send one static image to one Times Gate display."""

        _validate_panel_index(panel_index)
        _validate_image_size(image)

        lcd_array = [0] * PANEL_COUNT
        lcd_array[panel_index] = 1

        payload = {
            "Command": "Draw/SendHttpGif",
            "LocalToken": self._config.local_token,
            "LcdArray": lcd_array,
            "PicNum": 1,
            "PicWidth": PANEL_SIZE,
            "PicOffset": 0,
            "PicID": self._new_picture_id(),
            "PicSpeed": 1000,
            "PicData": encode_image(image),
        }

        return self._post(payload)

    def _new_picture_id(self) -> int:
        picture_id = self._next_picture_id
        self._next_picture_id += 1
        return picture_id

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            url=self._config.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self._config.timeout_seconds,
            ) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as error:
            raise TimesGateError(
                f"Times Gate returned HTTP {error.code}: {error.reason}"
            ) from error
        except URLError as error:
            raise TimesGateError(
                f"Could not reach Times Gate at {self._config.api_url}: {error.reason}"
            ) from error
        except TimeoutError as error:
            raise TimesGateError(
                f"Connection to Times Gate at {self._config.api_url} timed out"
            ) from error

        try:
            response_data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise TimesGateError(f"Times Gate returned invalid JSON: {response_body!r}") from error

        if not isinstance(response_data, dict):
            raise TimesGateError("Times Gate returned an unexpected response")

        _raise_for_api_error(response_data)

        return response_data


def encode_image(image: Image.Image) -> str:
    """Encode a Pillow image as a Base64 JPEG."""

    buffer = io.BytesIO()

    image.convert("RGB").save(
        buffer,
        format="JPEG",
        quality=90,
    )

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _validate_panel_index(panel_index: int) -> None:
    if not 0 <= panel_index < PANEL_COUNT:
        raise ValueError(f"Panel index must be between 0 and {PANEL_COUNT - 1}")


def _validate_image_size(image: Image.Image) -> None:
    expected_size = (PANEL_SIZE, PANEL_SIZE)

    if image.size != expected_size:
        raise ValueError(f"Image has size {image.size}; expected {expected_size}")


def _raise_for_api_error(response_data: dict[str, Any]) -> None:
    return_code = response_data.get(
        "ReturnCode",
        response_data.get("error_code"),
    )

    if return_code in (None, 0):
        return

    message = response_data.get(
        "ReturnMessage",
        response_data.get(
            "error_message",
            "unknown error",
        ),
    )

    raise TimesGateError(f"Times Gate rejected the request with code {return_code}: {message}")
