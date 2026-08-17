# Novachrono

Novachrono is a self-hosted dashboard renderer for the [Divoom Times Gate](https://divoom.com/).

It renders a consistent five-screen dashboard, generates local previews, and sends individual or complete dashboard panels to a Times Gate through its local network API.

> Novachrono is currently in an early development stage. Features, configuration, and architecture may change before the first stable release.

## Current Status

The following functionality is currently available:

- rendering of five 128 × 128 pixel panels
- shared custom HUD-style visual design
- current weather widget using live Open-Meteo data
- Celsius and Fahrenheit display support
- German and English UI localization
- clock and date widget
- Pokémon GO raid boss widget using live ScrapedDuck and PokéAPI data
- combined local dashboard preview
- targeted image upload to individual Times Gate displays
- complete five-display dashboard upload
- local Times Gate connection check
- `.env`-based configuration
- command-line interface powered by Typer
- automated tests with pytest
- formatting and linting with Ruff
- security checks with Bandit and pip-audit

The current display assignment is:

1. **Placeholder**
2. **Current weather**
3. **Clock and date**
4. **Pokémon GO raids**
5. **Placeholder**

All panels use the same custom Novachrono design rather than reproducing the standard Divoom dashboard.

## Goals

Novachrono aims to provide:

- a coherent visual interface across all five Times Gate displays
- independently rendered 128 × 128 pixel widgets
- local previews without requiring a physical Times Gate
- configurable data sources and display settings
- resilient handling of unavailable APIs and network services
- simple deployment on a Raspberry Pi or another always-on device
- a small and understandable Python codebase
- clear separation between rendering, configuration, data retrieval, and device communication

## Non-Goals

Novachrono is not intended to be:

- a general-purpose home automation platform
- a replacement for the official Divoom application
- a network-attached storage solution
- an enterprise dashboard framework
- a universal plugin platform
- dependent on a specific hosting device

A Raspberry Pi may run Novachrono alongside other services, but those services are outside the scope of this repository.

## How It Works

Novachrono does not install applications directly on the Times Gate.

It runs on another device in the same local network:

```text
External data sources
        |
        v
   Novachrono
        |
        +-- loads configuration
        +-- retrieves and normalizes data
        +-- renders five 128 x 128 pixel images
        +-- generates a local dashboard preview
        +-- sends selected images to the Times Gate
        |
        v
Divoom Times Gate
```

Each Times Gate display can be updated independently.

The current implementation can send individual rendered panels or the complete dashboard. Automatic scheduling, change detection, retries, and recovery behavior are planned.

## Architecture

The source tree separates the main responsibilities:

```text
src/novachrono/
├── __init__.py
├── __main__.py
├── cli.py
├── config.py
├── dashboard.py
├── i18n.py
├── pokemon_go.py
├── preview.py
├── units.py
├── weather.py
├── design/
│   ├── __init__.py
│   ├── components.py
│   └── theme.py
├── outputs/
│   ├── __init__.py
│   └── times_gate.py
├── sources/
│   ├── __init__.py
│   ├── open_meteo.py
│   ├── pokeapi.py
│   ├── pokemon_artwork.py
│   └── scraped_duck.py
└── widgets/
    ├── __init__.py
    ├── clock.py
    ├── pokemon_go/
    │   ├── __init__.py
    │   └── raid_bosses.py
    └── weather/
        ├── __init__.py
        ├── current.py
        └── icons.py
```

### Widgets

Widgets render 128 × 128 pixel Pillow images.

They do not communicate directly with the Times Gate.

Current widgets:

- current weather
- clock and date
- Pokémon GO raids

Planned widgets include:

- GitHub status
- calendar information
- system status

### Weather Data

Current weather data is provided by [Open-Meteo](https://open-meteo.com/).

Novachrono retrieves current temperature, weather conditions, daily high and low
temperatures, precipitation probability, and day/night information. Provider-specific
weather codes are normalized before they reach the widget renderer.

Open-Meteo data is provided under the
[CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).

### Design

The `design` package contains visual elements shared between widgets:

- common HUD frame
- widget headers
- colors
- panel dimensions
- reusable design constants

Widget-specific geometry remains inside the corresponding widget unless it becomes genuinely reusable.

### Dashboard

The dashboard renderer creates the five panel images and assigns widgets to displays.

Current assignments:

```text
Panel index 0 -> placeholder
Panel index 1 -> weather
Panel index 2 -> clock
Panel index 3 -> pokemon_go
Panel index 4 -> placeholder
```

The physical displays are therefore numbered 1 through 5, while the internal panel indices range from 0 through 4.

### Configuration

`config.py` loads application settings from:

1. `.env`
2. process environment variables

Process environment variables override values from `.env`.

Configuration is normalized into an immutable `AppConfig` before it is used by the application.

### Internationalization

Small UI strings are translated through `i18n.py`.

Currently supported locales:

```text
de_DE
en_US
```

The current localized widget text is the weather title:

```text
de_DE -> WETTER
en_US -> WEATHER
```

The clock currently uses a numeric time and date representation and therefore does not require locale-specific date formatting.

### Units

Temperatures are stored internally as Celsius values.

The display unit can be configured as:

```text
C
F
```

Fahrenheit values are converted during rendering. Weather typography adapts to wider values such as negative temperatures and three-digit Fahrenheit temperatures.

### Preview

The preview module combines all five panel images into one PNG file for local inspection.

This allows visual development and most automated testing without access to physical hardware.

### Output Adapters

Output adapters deliver rendered images to external destinations.

The Times Gate adapter:

- communicates through the local Times Gate HTTP API
- validates panel numbers and image dimensions
- encodes panel images as Base64 JPEG data
- sends images to individual displays
- translates network and device errors into application-specific exceptions

### Command-Line Interface

The CLI is implemented with Typer.

Current commands:

```text
preview
check-device
send-clock
send-weather
send-pokemon
send-dashboard
```

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- a Divoom Times Gate connected to the same local network for device-related commands
- local API access enabled in the Divoom application
- a local Times Gate token

The project includes `tzdata` so that IANA time zones such as `Europe/Berlin` also work consistently on platforms such as Windows.

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

Novachrono automatically loads a `.env` file from the current working directory.

Create your local configuration from the provided example:

### PowerShell

```powershell
Copy-Item .env.example .env
```

### Bash or Zsh

```shell
cp .env.example .env
```

The currently supported settings are:

```dotenv
NOVACHRONO_LOCALE=de_DE
NOVACHRONO_TIMEZONE=Europe/Berlin
NOVACHRONO_TEMPERATURE_UNIT=C

NOVACHRONO_WEATHER_LATITUDE=53.04771
NOVACHRONO_WEATHER_LONGITUDE=8.80169

NOVACHRONO_TIMES_GATE_HOST=192.168.1.100
NOVACHRONO_TIMES_GATE_TOKEN=replace-me
```

### Locale

Supported values:

```text
de_DE
en_US
```

Default:

```text
de_DE
```

### Timezone

Use an IANA timezone name such as:

```text
Europe/Berlin
Europe/London
America/New_York
```

Default:

```text
Europe/Berlin
```

### Temperature Unit

Supported values:

```text
C
F
```

The configuration parser also accepts the aliases:

```text
CELSIUS
FAHRENHEIT
```

Values are case-insensitive.

Default:

```text
C
```

### Weather Location

Weather data is retrieved for the configured WGS84 coordinates:

```text
NOVACHRONO_WEATHER_LATITUDE
NOVACHRONO_WEATHER_LONGITUDE
```

### Times Gate Host

The host must contain only the local IP address or hostname.

Correct:

```text
192.168.1.100
times-gate.local
```

Do not include:

```text
http://
https://
:9000
/divoom_api
```

### Times Gate Token

The local Times Gate token is required for commands that communicate with the physical device.

Do not commit a real token.

### Environment Overrides

Process environment variables override values from `.env`.

For example:

```powershell
$env:NOVACHRONO_TEMPERATURE_UNIT = "F"
uv run novachrono preview
```

The Times Gate host and token can additionally be overridden through command-line options:

```shell
uv run novachrono check-device --host 192.168.1.100 --token replace-me
```

Using `--token` regularly is discouraged because command-line arguments may be stored in shell history or exposed to other processes.

## Usage

### Show Available Commands

```shell
uv run novachrono --help
```

### Generate a Local Dashboard Preview

```shell
uv run novachrono preview
```

The default output is:

```text
output/dashboard-preview.png
```

Choose another destination with:

```shell
uv run novachrono preview --output output/custom-preview.png
```

or:

```shell
uv run novachrono preview -o output/custom-preview.png
```

A physical Times Gate is not required to generate previews.

### Check the Times Gate Connection

```shell
uv run novachrono check-device
```

This sends a read-only configuration request to the configured Times Gate.

### Send the Clock Widget

```shell
uv run novachrono send-clock
```

The clock is currently assigned to physical display 3.

### Send the Weather Widget

```shell
uv run novachrono send-weather
```

The weather widget is currently assigned to physical display 2.

Weather data is retrieved from Open-Meteo using the configured coordinates.

### Send the Pokémon GO Widget

```shell
uv run novachrono send-pokemon
```

The Pokémon GO widget is currently assigned to physical display 4.

Raid data is retrieved from ScrapedDuck. Boss artwork is retrieved from the PokéAPI.

### Send the Complete Dashboard

```shell
uv run novachrono send-dashboard
```

This renders all five panels and sends them to the Times Gate one after another.

If one or more displays fail, Novachrono reports the affected display numbers.

### Run as a Python Module

The package also supports:

```shell
uv run python -m novachrono preview
```

## Local Development

Install the project and all development dependencies:

```shell
uv sync --locked --all-groups
```

Format the source code:

```shell
uv run ruff format .
```

Check formatting without modifying files:

```shell
uv run ruff format --check .
```

Run linting:

```shell
uv run ruff check .
```

Run security linting:

```shell
uv run bandit -r src
```

Audit Python dependencies:

```shell
uv run pip-audit
```

Run the test suite:

```shell
uv run pytest
```

Generate a dashboard preview:

```shell
uv run novachrono preview
```

A typical complete local verification is:

```shell
uv run ruff format --check .
uv run ruff check .
uv run bandit -r src
uv run pip-audit
uv run pytest
uv run novachrono preview
```

Most tests do not require access to a physical Times Gate. Network calls to the device are mocked in the test suite.

## Testing

The test suite currently covers:

- CLI behavior
- application configuration
- Celsius and Fahrenheit conversion
- negative and three-digit temperatures
- internationalization
- dashboard composition
- weather rendering
- Open-Meteo request, response, and weather-code handling
- clock rendering
- shared design invariants
- preview generation
- Times Gate request generation
- Times Gate response and error handling

Renderer tests focus primarily on behavior and deterministic output instead of maintaining large fragile pixel snapshots.

A small targeted pixel regression test protects the continuity of the shared HUD frame because this has previously been a real rendering regression.

## Security

Never commit:

- Divoom local tokens
- GitHub personal access tokens
- private calendar feed URLs
- credentials
- `.env`
- local configuration containing personal data

`.env.example` contains documentation values only and is intended to remain in version control.

If a real token is accidentally committed, revoke or replace it where possible. Removing the token only from the latest source file does not remove it from Git history.

Potential security issues should be reported according to the [Security Policy](SECURITY.md).

## Roadmap

### Foundation

- [x] create Python project structure
- [x] render five 128 × 128 panels
- [x] create a shared Novachrono HUD design
- [x] generate a combined dashboard preview
- [x] add automated formatting, linting, testing, and security checks
- [x] add a Typer-based CLI
- [x] add `.env`-based configuration
- [x] add basic internationalization
- [x] add configurable Celsius and Fahrenheit rendering

### Clock Widget

- [x] render current time and date
- [x] place the clock on display 3
- [x] refine typography and spacing for the physical display
- [x] integrate the shared HUD frame

### Weather Widget

- [x] create current-weather widget
- [x] render weather conditions with custom icons
- [x] render current temperature
- [x] render high and low temperatures
- [x] render precipitation probability
- [x] support Celsius and Fahrenheit
- [x] support localized widget title
- [x] refine layout for the physical display
- [x] connect a real weather data source
- [x] map provider weather conditions to the internal weather model
- [x] remove demo weather data

### Times Gate Integration

- [x] connect through the local Times Gate API
- [x] authenticate with the local token
- [x] check device connectivity
- [x] send an image to an individual display
- [x] send the complete dashboard
- [ ] avoid sending unchanged images
- [ ] add retry and recovery behavior

### Additional Widgets

- [x] research a reliable Pokémon GO event data source
- [x] render current raid information
- [x] render Pokémon GO raid bosses widget
- [ ] implement GitHub status data
- [ ] add configurable calendar or system-status widgets

### Runtime and Deployment

- [ ] add scheduled dashboard updates
- [ ] make update intervals configurable
- [ ] add structured logging
- [ ] support graceful shutdown
- [ ] document Raspberry Pi installation
- [ ] provide a systemd service example
- [ ] optionally provide a container image

## Planned Configuration

Future configuration may include:

- GitHub repositories and token
- calendar feeds
- widget update intervals
- display assignments
- visual theme settings

The existing environment-variable configuration should remain small and understandable. Additional structure should only be introduced when the project genuinely requires it.

## Contributing

Contributions are welcome.

Before contributing, please read:

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Support and Help](SUPPORT.md)

## Project Name

The name Novachrono is inspired by Julius Novachrono and his association with time magic in *Black Clover*.

The name also reflects the project's relationship with the Divoom Times Gate and its focus on time-based and contextual information.

## Trademarks and Third-Party Services

Novachrono is an independent hobby project.

It is not affiliated with, endorsed by, or sponsored by:

- Divoom
- Nintendo
- The Pokémon Company
- Niantic
- GitHub
- the creators or publishers of *Black Clover*

Product names, trademarks, logos, and other third-party assets belong to their respective owners.

Third-party images, fonts, icons, APIs, feeds, and other assets must only be included when their licenses and terms permit redistribution.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## License

Novachrono is licensed under the [MIT License](LICENSE).
