# Novachrono

Novachrono is a self-hosted dashboard renderer for the [Divoom Times Gate](https://divoom.com/).

It renders a consistent five-screen dashboard, generates local previews, and sends individual panel images to the Times Gate through its local network API.

> Novachrono is currently in an early development stage. Features, configuration, and architecture may change before the first stable release.

## Current Status

The following functionality is already available:

- rendering of five 128 × 128 pixel panels
- combined local dashboard preview
- localized clock and date widget
- targeted image upload to individual Times Gate displays
- local Times Gate connection check
- command-line interface powered by Typer
- automated tests with pytest
- formatting and linting with Ruff
- security checks with Bandit and pip-audit
- CI on Windows and Linux
- software bill of materials generation

The current dashboard uses the center display for the clock. The remaining panels are placeholders until additional widgets are implemented.

## Planned Dashboard

The first complete dashboard is expected to use the five Times Gate displays approximately as follows:

1. **Current weather**
2. **Weather forecast**
3. **Clock and date**
4. **GitHub status**
5. **Pokémon GO events, calendar information, or system status**

The final display assignment should eventually become configurable.

All screens should share a consistent custom Novachrono design rather than reproduce the standard Divoom dashboard.

## Goals

Novachrono aims to provide:

- a coherent visual interface across all five Times Gate displays
- independently rendered 128 × 128 pixel widgets
- local previews without requiring a physical Times Gate
- configurable data sources and update intervals
- resilient handling of unavailable APIs and network services
- simple deployment on a Raspberry Pi or another always-on device
- a small and understandable Python codebase
- clear separation between data retrieval, rendering, and device communication

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
        +-- loads and normalizes data
        +-- renders five 128 x 128 pixel images
        +-- generates a local dashboard preview
        +-- sends selected images to the Times Gate
        |
        v
Divoom Times Gate
```

Each Times Gate display can be updated independently.

The current implementation already supports sending a rendered image to a selected display. Automatic update scheduling and change detection are planned.

## Architecture

The current source structure separates the main responsibilities:

```text
src/novachrono/
├── cli.py
├── dashboard.py
├── design.py
├── preview.py
├── outputs/
│   └── times_gate.py
└── widgets/
    └── clock.py
```

### Widgets

Widgets render 128 × 128 pixel Pillow images.

They should not communicate directly with external APIs or the Times Gate.

Current widget:

- clock and localized date

Planned widgets include:

- current weather
- weather forecast
- GitHub status
- Pokémon GO events
- calendar information
- system status

### Dashboard

The dashboard renderer creates the five panel images and assigns widgets to displays.

The clock currently occupies the center display, which uses panel index `2`.

### Preview

The preview module combines all five panel images into one PNG file for local inspection.

This allows most visual development and automated testing without access to physical hardware.

### Output Adapters

Output adapters deliver rendered images to external destinations.

The current Times Gate adapter:

- communicates through the local Times Gate HTTP API
- validates panel numbers and image dimensions
- encodes panel images as Base64 JPEG data
- sends images to individual displays
- translates network and device errors into application-specific exceptions

### Command-Line Interface

The CLI provides commands for rendering previews, checking the device connection, and sending the clock widget.

It is implemented with Typer.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- a Divoom Times Gate connected to the same local network
- local API access enabled in the Divoom application
- a local Times Gate token

The project includes `tzdata` so that IANA time zones such as `Europe/Berlin` also work on Windows.

## Installation

Clone the repository:

```shell
git clone https://github.com/drachenpapa/novachrono.git
cd novachrono
```

Install the locked dependencies:

```shell
uv sync --locked --all-groups
```

Verify the installation:

```shell
uv run novachrono --help
```

## Configuration

The Times Gate connection is currently configured through environment variables:

```text
NOVACHRONO_TIMES_GATE_HOST
NOVACHRONO_TIMES_GATE_TOKEN
```

The host must contain only the IP address or hostname, without `http://`, a port, or an API path.

### PowerShell

```powershell
$env:NOVACHRONO_TIMES_GATE_HOST = "192.168.x.x"
$env:NOVACHRONO_TIMES_GATE_TOKEN = "replace-me"
```

### Bash or Zsh

```shell
export NOVACHRONO_TIMES_GATE_HOST="192.168.x.x"
export NOVACHRONO_TIMES_GATE_TOKEN="replace-me"
```

Command-line options may also override these values:

```shell
uv run novachrono check-device --host 192.168.x.x --token replace-me
```

Using `--token` regularly is discouraged because the value may be stored in shell history.

Never commit the real local token, IP-specific configuration, private API keys, or personal feed URLs.

## Usage

### Show available commands

```shell
uv run novachrono --help
```

### Generate a local dashboard preview

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

### Check the Times Gate connection

```shell
uv run novachrono check-device
```

This sends a read-only configuration request to the locally configured Times Gate.

### Send the clock widget

```shell
uv run novachrono send-clock
```

This renders the current clock panel and sends it to display 3.

### Run as a Python module

The package also supports:

```shell
uv run python -m novachrono preview
```

## Local Development

Install all project and development dependencies:

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

Run all common local checks:

```shell
uv run ruff format --check .
uv run ruff check .
uv run bandit -r src
uv run pip-audit
uv run pytest
uv run novachrono preview
```

Most tests do not require access to a physical Times Gate. Network calls are mocked in the test suite.

## Continuous Integration

GitHub Actions currently performs:

- Ruff formatting checks
- Ruff linting
- Bandit security analysis
- dependency auditing with pip-audit
- tests on Ubuntu and Windows
- dashboard preview generation
- pull-request dependency review
- SBOM generation

CI does not connect to a real Times Gate and does not require device credentials.

## Environment Example

An `.env.example` file documents the required connection values:

```dotenv
NOVACHRONO_TIMES_GATE_HOST=192.168.x.x
NOVACHRONO_TIMES_GATE_TOKEN=replace-me
```

Novachrono does not currently load `.env` files automatically. The file serves as a configuration example only.

## Security

Do not commit:

- Divoom local tokens
- GitHub personal access tokens
- weather API keys
- private calendar feed URLs
- credentials
- local environment files
- configuration containing personal data

If a real token was accidentally committed, remove it from use and generate or configure a replacement where possible. Removing it only from the latest source file does not remove it from Git history.

Potential security issues should be reported according to the [Security Policy](SECURITY.md).

## Roadmap

### Foundation

- [x] create Python project structure
- [x] render five 128 × 128 panels
- [x] generate a combined dashboard preview
- [x] add automated formatting, linting, testing, and security checks
- [x] add a Typer-based CLI

### Clock Widget

- [x] render current time and date
- [x] localize weekday and date with Babel
- [x] place the clock on display 3
- [ ] refine typography and spacing on the physical display
- [ ] extract shared widget-rendering primitives

### Times Gate Integration

- [x] connect through the local Times Gate API
- [x] authenticate with the local token
- [x] check device connectivity
- [x] send an image to an individual display
- [ ] send the complete dashboard
- [ ] avoid sending unchanged images
- [ ] add retry and recovery behavior

### External Data

- [ ] implement a weather data service
- [ ] render current weather
- [ ] render a weather forecast
- [ ] implement GitHub status data
- [ ] render assigned issues, pull requests, or workflow status
- [ ] research a reliable Pokémon GO event data source
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

- Times Gate host
- local token
- timezone
- locale
- weather coordinates
- weather API credentials
- GitHub repositories and token
- calendar feeds
- widget update intervals
- display assignments
- visual theme settings

A future structure may resemble:

```yaml
timezone: Europe/Berlin
locale: de_DE

times_gate:
  host: 192.168.1.100

widgets:
  weather_current:
    display: 1
    update_interval_minutes: 15

  weather_forecast:
    display: 2
    update_interval_minutes: 30

  clock:
    display: 3
    update_interval_minutes: 1

  github:
    display: 4
    update_interval_minutes: 10
```

This example is illustrative and does not represent a stable configuration format.

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

## License

Novachrono is licensed under the [MIT License](LICENSE).
