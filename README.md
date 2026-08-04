# Novachrono

Novachrono is a self-hosted dashboard renderer for the [Divoom Times Gate](https://divoom.com/).

It generates a consistent five-screen interface for information such as weather, time, Pokémon GO events, developer workflow metrics, and other configurable data sources.

> Novachrono is currently in an early development stage. Features, configuration, and architecture may change before the first stable release.

## Planned Dashboard

The initial dashboard is intended to use the five Times Gate displays as follows:

1. **Weather**
2. **Clock and date**
3. **Current or upcoming Pokémon GO event**
4. **Assigned GitHub issues and pull requests**
5. **Configurable contextual information**

The fifth screen may later display information such as:

* the next calendar event
* a focus timer
* system status
* notifications
* another configurable widget

All screens should share a consistent visual design.

## Goals

Novachrono aims to provide:

* a coherent visual interface across all five Times Gate displays
* independently rendered 128 × 128 pixel widgets
* local previews without requiring a physical Times Gate
* configurable data sources and update intervals
* resilient handling of unavailable APIs and network services
* simple deployment on a Raspberry Pi or another always-on device
* a small and understandable Python codebase

## Non-Goals

Novachrono is not intended to be:

* a general-purpose home automation platform
* a replacement for the official Divoom application
* a network-attached storage solution
* an enterprise dashboard framework
* a universal plugin platform
* dependent on a specific hosting device

A Raspberry Pi may run Novachrono alongside other services, but those services are outside the scope of this repository.

## How It Works

Novachrono does not install applications directly on the Times Gate.

Instead, it runs on another device in the same local network:

```text
External data sources
        |
        v
Novachrono
        |
        +-- loads and normalizes data
        +-- renders five 128 x 128 pixel images
        +-- generates a local dashboard preview
        +-- sends changed images to the Times Gate
        |
        v
Divoom Times Gate
```

Each display can be updated independently.

For example:

* the clock may update every minute
* weather may update every 15 to 30 minutes
* Pokémon GO events may update when calendar data changes
* GitHub metrics may update every few minutes
* unchanged images do not need to be transmitted again

## Architecture

Novachrono is expected to consist conceptually of four areas:

```text
Data sources
    |
    v
Application models
    |
    v
Widget rendering
    |
    v
Output adapters
```

### Data Sources

Data sources retrieve information from external services, feeds, or local configuration.

Possible examples include:

* weather APIs
* iCalendar or ICS feeds
* GitHub APIs
* local system information

### Application Models

External data is converted into small internal models.

Renderers should not depend directly on raw API or calendar responses.

### Widget Rendering

Each widget renders a 128 × 128 pixel image.

Rendering should work independently of the Times Gate so that widgets can be developed and tested using local preview images.

### Output Adapters

Output adapters deliver rendered images to their destination.

The initial outputs are expected to be:

* local PNG preview files
* a combined five-screen dashboard preview
* the Divoom Times Gate

## Planned Development Stages

### Stage 1: Static Preview

* create the Python project structure
* define the shared visual design
* render five static 128 × 128 pixel panels
* generate a combined dashboard preview

### Stage 2: Clock Widget

* render the current time and date
* support a configurable timezone
* update at the beginning of each minute

### Stage 3: Times Gate Integration

* configure the Times Gate network address
* send a test image to an individual display
* update displays independently
* avoid sending unchanged images

### Stage 4: External Data

* add weather information
* add Pokémon GO calendar events
* add assigned GitHub issues and pull requests
* handle unavailable or incomplete external data

### Stage 5: Deployment

* provide a documented Raspberry Pi setup
* optionally provide a container image or Docker Compose configuration
* support unattended execution and automatic restarts

## Technology

The initial implementation is planned in Python.

Specific libraries, development tools, and supported Python versions will be documented once the initial project setup has been defined.

Likely areas include:

* image rendering
* HTTP communication
* calendar parsing
* configuration management
* scheduling
* automated testing

Dependencies should remain small, intentional, and actively maintained.

## Configuration

Runtime configuration must not be hard-coded into the source code.

Configuration may later include:

* Times Gate host or IP address
* Times Gate device token, if required
* local timezone
* weather location
* weather API credentials
* GitHub account and access token
* Pokémon GO calendar feed
* widget update intervals
* display assignments
* visual theme settings

Secrets and machine-specific values must not be committed to the repository.

A future configuration structure may resemble:

```yaml
timezone: Europe/Berlin

times_gate:
  host: 192.168.1.100

widgets:
  weather:
    display: 1
    update_interval_minutes: 20

  clock:
    display: 2

  pokemon_go:
    display: 3
    update_interval_minutes: 15

  github:
    display: 4
    update_interval_minutes: 10
```

This example is illustrative and does not yet represent a stable configuration format.

## Local Development

The first development milestone is a local five-panel preview.

A physical Times Gate should not be required to:

* develop widget layouts
* test rendering logic
* inspect generated images
* run most automated tests

Once the Python project setup is available, installation and execution commands will be documented here.

## Security

Do not commit:

* GitHub personal access tokens
* weather API keys
* Divoom device tokens
* private calendar feed URLs
* credentials
* local environment files
* configuration containing personal data

Potential security issues should be reported according to the [Security Policy](SECURITY.md).

## Contributing

Contributions are welcome.

Before contributing, please read:

* [Contributing Guidelines](CONTRIBUTING.md)
* [Code of Conduct](CODE_OF_CONDUCT.md)
* [Support and Help](SUPPORT.md)

## Project Name

The name Novachrono is inspired by Julius Novachrono and his association with time magic in *Black Clover*.

The name also reflects the project's relationship with the Divoom Times Gate and its focus on time-based and contextual information.

## Trademarks and Third-Party Services

Novachrono is an independent hobby project.

It is not affiliated with, endorsed by, or sponsored by:

* Divoom
* Nintendo
* The Pokémon Company
* Niantic
* GitHub
* the creators or publishers of *Black Clover*

Product names, trademarks, logos, and other third-party assets belong to their respective owners.

Third-party images, fonts, icons, APIs, feeds, and other assets must only be included when their licenses and terms permit redistribution.

## License

Novachrono is licensed under the [MIT License](LICENSE).
