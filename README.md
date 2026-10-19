# Novachrono

Novachrono is a self-hosted dashboard renderer for the [Divoom Times Gate](https://divoom.com/).

It renders a consistent five-screen dashboard, generates local previews, and sends static or animated widgets to a Times Gate through its local network API.

> Novachrono is currently in an early development stage. Features and configuration may change before the first stable release.

## Current Dashboard

Novachrono renders five 128 × 128 pixel panels:

1. Placeholder
2. Current weather
3. Clock and date
4. Pokémon GO raids
5. Pokémon GO events

All panels use the same custom HUD-style design.

Current widgets include:

- current weather from Open-Meteo
- animated rain and fog
- Celsius and Fahrenheit support
- German and English UI and date formatting
- local time and date
- Pokémon GO five-star, Shadow five-star, and Mega raids
- Pokémon GO Community Days
- Pokémon GO Community Day Classics
- Pokémon GO Spotlight Hours
- Pokémon GO Max Mondays
- localized Pokémon names through PokeAPI
- Pokémon artwork from ScrapedDuck and PokeAPI
- shiny availability indicators
- native raid rotation when multiple bosses are active
- native event rotation when multiple events or featured Pokémon are active

Pokémon GO event data is reduced to the current or next relevant occurrence for each supported event category. Unsupported events and incomplete external event entries are ignored.

## Architecture

The project keeps configuration, data retrieval, models, rendering, orchestration, and device communication separate:

```text
External data sources
        |
        v
     sources/
        |
        v
      models/
        |
        v
      widgets/
        |
        v
 Pillow images / frames
        |
        +-- preview
        |
        +-- CLI orchestration
                |
                v
             outputs/
                |
                v
         Divoom Times Gate
```

Current source structure:

```text
src/novachrono/
├── __init__.py
├── __main__.py
├── cli/
│   ├── __init__.py
│   ├── _common.py
│   ├── dashboard.py
│   └── widgets.py
├── config.py
├── dashboard.py
├── display_state.py
├── i18n.py
├── preview.py
├── units.py
├── design/
├── models/
├── outputs/
├── sources/
│   ├── open_meteo.py
│   ├── pokeapi/
│   ├── pokemon_artwork.py
│   └── scraped_duck/
└── widgets/
    ├── clock.py
    ├── pokemon_go/
    └── weather/
```

Widgets only render images and animation frames. Network access is handled by source and output adapters.

The CLI coordinates data retrieval, rendering, state comparison, and delivery without putting those responsibilities into the renderers themselves.

## Requirements

- Python 3.15
- [uv](https://docs.astral.sh/uv/) 0.13.1 or newer
- Divoom Times Gate for device-related commands
- local Times Gate API access and token

Python runtime upgrades must keep `pyproject.toml`, `.python-version`, and `uv.lock`
aligned. Renovate groups the requirement and interpreter-pin updates together.
CI installs the interpreter from `.python-version`, and Ruff infers its Python
target from `pyproject.toml`.

PyYAML's optional C extension is disabled for source builds so the development
tools can be installed without a native compiler while Python 3.15 wheels are
unavailable.

## Installation

Clone the repository:

```shell
git clone https://github.com/drachenpapa/novachrono.git
cd novachrono
```

Install the locked project and development dependencies:

```shell
uv sync --locked --all-groups
```

Verify the installation:

```shell
uv run novachrono --help
```

## Configuration

Novachrono loads configuration from `.env` and process environment variables.

Create a local configuration:

### PowerShell

```powershell
Copy-Item .env.example .env
```

### Bash or Zsh

```shell
cp .env.example .env
```

Supported settings:

```dotenv
NOVACHRONO_LOCALE=de_DE
NOVACHRONO_TIMEZONE=Europe/Berlin
NOVACHRONO_TEMPERATURE_UNIT=C

NOVACHRONO_WEATHER_LATITUDE=53.04771
NOVACHRONO_WEATHER_LONGITUDE=8.80169

NOVACHRONO_TIMES_GATE_HOST=192.168.1.100
NOVACHRONO_TIMES_GATE_TOKEN=replace-me
```

Supported temperature-unit values are:

```text
C
CELSIUS
F
FAHRENHEIT
```

Values are case-insensitive.

Process environment variables override values from `.env`.

Never commit a real Times Gate token or `.env` file.

## Usage

Show available commands:

```shell
uv run novachrono --help
```

Available commands include:

```text
preview
check-device
send-dashboard
send-clock
send-pokemon-events
send-pokemon-raids
send-weather
```

### Preview

Generate a combined local dashboard preview:

```shell
uv run novachrono preview
```

Default output:

```text
output/dashboard-preview.png
```

A physical Times Gate is not required.

The preview retrieves the same external weather and Pokémon GO data used by the physical dashboard.

### Check Device

```shell
uv run novachrono check-device
```

Checks communication with the configured Times Gate and returns its current device configuration.

The configured Times Gate host and token can be overridden for an individual invocation:

```shell
uv run novachrono check-device --host 192.168.1.100 --token replace-me
```

### Clock

```shell
uv run novachrono send-clock
```

Sends the current clock panel to display 3.

The clock includes locale-aware date formatting and is always sent.

### Weather

```shell
uv run novachrono send-weather
```

Sends the weather widget to display 2.

If the rendering-relevant weather state has not changed since the previous successful delivery, the device update is skipped.

Force an update with:

```shell
uv run novachrono send-weather --force
```

Rain uses a native three-frame animation and fog uses a native ten-frame animation.

### Pokémon GO Raids

```shell
uv run novachrono send-pokemon-raids
```

Sends the Pokémon GO raid widget to display 4.

The widget supports:

- five-star raids
- Shadow five-star raids
- Mega raids
- localized Pokémon names
- artwork
- shiny indicators
- rotation through multiple active bosses

The raid roster is localized before its rendering-relevant state is compared with the previously delivered state.

If that state has not changed, artwork retrieval, rendering, and device transfer are skipped.

Force an update with:

```shell
uv run novachrono send-pokemon-raids --force
```

Multiple active raid bosses are sent as native Times Gate animation frames.

### Pokémon GO Events

```shell
uv run novachrono send-pokemon-events
```

Sends the Pokémon GO event widget to display 5.

Supported event categories are:

- Community Day
- Community Day Classic
- Spotlight Hour
- Max Monday

Novachrono selects the current or next occurrence of each available category.

If an occurrence contains multiple featured Pokémon, each Pokémon receives its own animation frame.

Event frames rotate every 30 seconds.

If the rendering-relevant event schedule has not changed since the previous successful delivery, artwork retrieval, rendering, and device transfer are skipped.

Force an update with:

```shell
uv run novachrono send-pokemon-events --force
```

### Complete Dashboard

```shell
uv run novachrono send-dashboard
```

Sends all five displays.

`send-dashboard` always performs a full synchronization, regardless of cached state.

Static widgets are sent as individual images. Widgets with multiple frames are transferred using the native Times Gate animation protocol.

If an individual display fails, Novachrono retries the delivery once after five seconds. If the retry also fails, the remaining displays are still processed.

The command exits with an error after all remaining displays have been attempted if one or more displays could not be updated.

## Display State

Weather, Pokémon GO raids, and Pokémon GO events use small local state files to avoid unnecessary device updates:

```text
~/.novachrono/
├── events.state
├── raids.state
└── weather.state
```

Each file contains only a SHA-256 fingerprint of the last successfully delivered rendering-relevant state.

The fingerprints include the configuration that can influence the respective output, such as locale or temperature unit where applicable.

State is only updated after the corresponding display has been delivered successfully.

`send-dashboard` ignores cached state and can therefore be used to fully resynchronize the physical device. Successful dashboard delivery also refreshes the state of the weather, raid, and event panels.

## External Data Sources

Novachrono currently uses:

- [Open-Meteo](https://open-meteo.com/) for current weather
- [ScrapedDuck](https://github.com/bigfoott/ScrapedDuck) for Pokémon GO raid and event data
- [PokeAPI](https://pokeapi.co/) for Pokémon localization and missing Pokémon artwork metadata

Downloaded Pokémon artwork is normalized before rendering.

Source adapters validate external responses and isolate provider-specific data formats from the rest of the application.

Because external community-maintained data can occasionally contain incomplete entries, unsupported Pokémon GO events and supported events without usable timestamps are ignored rather than preventing the entire dashboard from rendering.

## Scheduling

Novachrono commands are intentionally one-shot operations.

There is no permanently running Python scheduler.

The intended Raspberry Pi deployment uses external scheduling, preferably systemd services and timers.

Example update intervals:

```text
clock    every minute
weather  every 15 minutes
raids    every hour
events   every hour
```

Weather, raid, and event state detection prevents unchanged content from being sent repeatedly even when their commands run on a fixed schedule.

A periodic `send-dashboard` invocation can additionally be used as a full synchronization.

## Local Development

Format code:

```shell
uv run ruff format .
```

Run the complete local verification:

```shell
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run bandit -r src
uv run pip-audit
```

A local unpublished `novachrono` package may appear as skipped in `pip-audit`; external dependencies are still audited.

Hardware-related changes should additionally be tested against a physical Times Gate.

For an end-to-end live-data and hardware check:

```shell
uv run novachrono send-dashboard
```

## Testing

The automated test suite covers, among other things:

- configuration and validation
- dashboard composition
- widget rendering
- locale-dependent rendering
- native weather, raid, and event animations
- external source adapters
- ScrapedDuck event and raid parsing
- Pokémon localization and artwork
- display-state fingerprints
- change detection
- Times Gate request payloads and error handling
- delivery retry behavior
- CLI routing and orchestration

Tests use mocked external services and do not require access to real APIs or a physical Times Gate.

Live external-data behavior and hardware communication should additionally be verified with the corresponding CLI commands.

## Roadmap

Completed:

- shared five-panel HUD design
- clock widget
- weather widget
- Pokémon GO raid widget
- Pokémon GO event widget
- Community Day, Community Day Classic, Spotlight Hour, and Max Monday support
- German and English rendering
- Pokémon name localization
- live external data sources
- native Times Gate animations
- persistent change detection
- forced widget refreshes
- device-delivery retry
- full-dashboard synchronization
- modular CLI, source, output, and widget architecture

Next:

- Raspberry Pi deployment documentation
- systemd services and timers
- serialization of simultaneous device updates
- full synchronization after boot
- additional widgets

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## License

Novachrono is licensed under the [MIT License](LICENSE).
