import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from PIL import Image

from novachrono.config import (
    TIMES_GATE_HOST_VARIABLE,
    TIMES_GATE_TOKEN_VARIABLE,
    WEATHER_LATITUDE_VARIABLE,
    WEATHER_LONGITUDE_VARIABLE,
    AppConfig,
    ConfigError,
    load_config,
)
from novachrono.display_state import (
    StateError,
    read_fingerprint,
    write_fingerprint,
)
from novachrono.models.pokemon_go import (
    EventSchedule,
    RaidRoster,
)
from novachrono.models.weather import CurrentWeather
from novachrono.outputs.delivery import (
    deliver_frames_with_retry,
)
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
)
from novachrono.sources.open_meteo import (
    OpenMeteoError,
    fetch_current_weather,
)
from novachrono.sources.pokeapi import (
    add_missing_event_artwork,
    localize_event_schedule,
    localize_raid_roster,
)
from novachrono.sources.scraped_duck import (
    ScrapedDuckError,
    fetch_event_schedule,
    fetch_raid_roster,
)

HostOption = Annotated[
    str | None,
    typer.Option(
        "--host",
        help=("Override the Times Gate host configured with NOVACHRONO_TIMES_GATE_HOST."),
        metavar="HOST",
    ),
]

TokenOption = Annotated[
    str | None,
    typer.Option(
        "--token",
        help=("Override the Times Gate token configured with NOVACHRONO_TIMES_GATE_TOKEN."),
        metavar="TOKEN",
    ),
]

ForceOption = Annotated[
    bool,
    typer.Option(
        "--force",
        help="Send even if the cached display state is unchanged.",
    ),
]


def _send_widget_frames(
    *,
    client: TimesGateClient,
    panel_index: int,
    frames: tuple[Image.Image, ...],
    frame_duration_ms: int | None,
    name: str,
) -> None:
    display_number = panel_index + 1
    typer.echo(f"Sending {name.lower()} to display {display_number} ...")

    try:
        responses = deliver_frames_with_retry(
            client=client,
            panel_index=panel_index,
            frames=frames,
            frame_duration_ms=frame_duration_ms,
        )
    except TimesGateError as error:
        _exit_with_error(str(error))

    typer.echo(f"{name} sent successfully with {len(frames)} frame(s).")

    response_output: object
    response_output = responses[0] if len(responses) == 1 else responses
    typer.echo(json.dumps(response_output, indent=2, ensure_ascii=False))


def _load_current_weather(app_config: AppConfig) -> CurrentWeather:
    latitude = app_config.weather.latitude
    longitude = app_config.weather.longitude

    if latitude is None or longitude is None:
        missing_variables: list[str] = []

        if latitude is None:
            missing_variables.append(WEATHER_LATITUDE_VARIABLE)

        if longitude is None:
            missing_variables.append(WEATHER_LONGITUDE_VARIABLE)

        joined_variables = ", ".join(missing_variables)

        _exit_with_error(f"Missing required weather configuration: {joined_variables}")

    try:
        return fetch_current_weather(
            latitude=latitude,
            longitude=longitude,
            timezone=app_config.timezone,
        )
    except OpenMeteoError as error:
        _exit_with_error(str(error))


def _load_event_schedule(app_config: AppConfig) -> EventSchedule:
    try:
        schedule = fetch_event_schedule(now=datetime.now(app_config.timezone))
    except ScrapedDuckError as error:
        _exit_with_error(str(error))

    schedule = add_missing_event_artwork(schedule)

    return localize_event_schedule(schedule, locale=app_config.locale)


def _load_raw_raid_roster() -> RaidRoster:
    try:
        return fetch_raid_roster()
    except ScrapedDuckError as error:
        _exit_with_error(str(error))


def _load_raid_roster(app_config: AppConfig) -> RaidRoster:
    return localize_raid_roster(_load_raw_raid_roster(), locale=app_config.locale)


def _cached_fingerprint_matches(
    path: Path,
    fingerprint: str,
) -> bool:
    try:
        return read_fingerprint(path) == fingerprint
    except StateError as error:
        typer.echo(f"Warning: {error}", err=True)

        return False


def _write_fingerprint_or_warn(
    path: Path,
    fingerprint: str,
) -> None:
    try:
        write_fingerprint(path, fingerprint)
    except StateError as error:
        typer.echo(f"Warning: {error}", err=True)


def _load_app_config() -> AppConfig:
    try:
        return load_config()
    except ConfigError as error:
        _exit_with_error(str(error))


def _create_times_gate_client(
    *,
    app_config: AppConfig,
    host: str | None,
    local_token: str | None,
) -> TimesGateClient:
    resolved_host = _resolve_value(override=host, configured=app_config.times_gate.host)
    resolved_token = _resolve_value(
        override=local_token, configured=app_config.times_gate.local_token
    )

    if resolved_host is None or resolved_token is None:
        missing_variables: list[str] = []

        if resolved_host is None:
            missing_variables.append(TIMES_GATE_HOST_VARIABLE)

        if resolved_token is None:
            missing_variables.append(TIMES_GATE_TOKEN_VARIABLE)

        joined_variables = ", ".join(missing_variables)
        _exit_with_error(f"Missing required configuration: {joined_variables}")

    try:
        times_gate_config = TimesGateConfig(host=resolved_host, local_token=resolved_token)
    except ValueError as error:
        _exit_with_error(str(error))

    return TimesGateClient(times_gate_config)


def _resolve_value(
    *,
    override: str | None,
    configured: str | None,
) -> str | None:
    if override is None:
        return configured

    normalized_override = override.strip()

    if normalized_override:
        return normalized_override

    return configured


def _exit_with_error(message: str) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)

    raise typer.Exit(code=1)
