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
5. Placeholder

All panels use the same custom HUD-style design.

Current widgets include:

- current weather from Open-Meteo
- animated rain and fog
- Celsius and Fahrenheit support
- German and English UI text
- local time and date
- Pokémon GO five-star, Shadow five-star, and Mega raids
- localized Pokémon names through PokeAPI
- raid artwork supplied by ScrapedDuck
- native raid rotation when multiple bosses are active

## Architecture

The project keeps data retrieval, models, rendering, and device communication separate:

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
        +-- outputs/
                |
                v
         Divoom Times Gate
```

Current source structure:

```text
src/novachrono/
├── cli.py
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
└── widgets/
```

Widgets only render images and animation frames. Network access is handled by source and output adapters.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Divoom Times Gate for device-related commands
- local Times Gate API access and token

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

Process environment variables override values from `.env`.

Never commit a real Times Gate token or `.env` file.

## Usage

Show available commands:

```shell
uv run novachrono --help
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

### Check Device

```shell
uv run novachrono check-device
```

Checks communication with the configured Times Gate.

### Clock

```shell
uv run novachrono send-clock
```

Sends the current clock panel to display 3.

The clock is always sent.

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

### Pokémon GO

```shell
uv run novachrono send-pokemon
```

Sends the Pokémon GO raid widget to display 4.

If the current raid roster has not changed since the previous successful delivery, localization, artwork retrieval, rendering, and device transfer are skipped.

Force an update with:

```shell
uv run novachrono send-pokemon --force
```

When multiple raid bosses are active, the Times Gate rotates through native animation frames.

### Complete Dashboard

```shell
uv run novachrono send-dashboard
```

Sends all five displays.

`send-dashboard` always performs a full synchronization, regardless of cached state.

If an individual display fails, Novachrono retries the delivery once after five seconds and continues with the remaining displays if the retry also fails.

## Display State

Weather and Pokémon GO use small local state files to avoid unnecessary device updates:

```text
~/.novachrono/
├── weather.state
└── pokemon-go.state
```

Each file contains only a SHA-256 fingerprint of the last successfully delivered rendering-relevant state.

`send-dashboard` ignores cached state and can therefore be used to fully resynchronize the physical device.

## Scheduling

Novachrono commands are intentionally one-shot operations.

There is no permanently running Python scheduler.

The intended Raspberry Pi deployment uses external scheduling, preferably systemd services and timers.

Planned update intervals:

```text
clock    every minute
weather  every 15 minutes
pokemon  every hour
```

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

## Testing

The automated test suite covers, among other things:

- configuration
- dashboard composition
- widget rendering
- native animations
- external source adapters
- Pokémon localization and artwork
- display-state fingerprints
- change detection
- Times Gate requests and error handling
- retry behavior
- CLI routing

Tests do not require access to real external services or a physical Times Gate.

## Roadmap

Completed:

- shared five-panel HUD design
- clock widget
- weather widget
- Pokémon GO raid widget
- live external data sources
- native Times Gate animations
- persistent change detection
- forced widget refreshes
- device-delivery retry
- full-dashboard synchronization

Next:

- Raspberry Pi deployment documentation
- systemd services and timers
- serialization of simultaneous device updates
- full synchronization after boot
- additional widgets

## Project Name

The name Novachrono is inspired by Julius Novachrono and his association with time magic in *Black Clover*.

It also reflects the project's relationship with the Divoom Times Gate.

## Trademarks

Novachrono is an independent hobby project and is not affiliated with Divoom, Nintendo, The Pokémon Company, Niantic, or the creators or publishers of *Black Clover*.

Third-party names, trademarks, artwork, and other assets belong to their respective owners.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## License

Novachrono is licensed under the [MIT License](LICENSE).
