# AGENTS.md

## Purpose

This repository may be maintained with the help of AI coding agents.

Novachrono is a small open-source hobby project that renders a five-screen dashboard for the Divoom Times Gate.

It is designed to run locally on a development computer and later on a Raspberry Pi or another always-on device.

Keep the project small, explicit, understandable, and easy for a human maintainer to review.

## Priorities

When making changes, prioritize:

1. correctness
2. security
3. simplicity
4. readability
5. maintainability
6. testability
7. performance where relevant

Prefer pragmatic solutions over speculative architecture.

Use:

- KISS
- DRY with judgment
- YAGNI
- composition over inheritance
- standard-library features where practical
- explicit code over hidden magic

Avoid:

- unnecessary abstraction
- premature plugin systems
- enterprise patterns without a concrete need
- broad rewrites
- unrelated cleanup
- new dependencies without clear benefit
- abstractions created only to remove small amounts of harmless duplication

## Project Context

Before changing code, inspect the relevant surrounding files.

Important project files include:

```text
README.md
pyproject.toml
.env.example
src/novachrono/
tests/
```

Do not infer the architecture from a single module.

Distinguish clearly between:

- implemented behavior
- planned behavior
- assumptions
- recommendations

Do not implement roadmap items unless the requested change actually requires them.

## Architecture

Novachrono separates these concerns:

```text
Configuration
     |
     v
Source adapters
     |
     v
Normalized application models
     |
     v
Widget renderers
     |
     v
Pillow images / animation frames
     |
     +--> Local preview
     |
     +--> Output delivery
              |
              v
        Times Gate adapter
```

This is a conceptual structure, not a requirement to create an interface or class for every layer.

### Responsibilities

`config.py`

- loads and validates application configuration
- centralizes environment-variable access

`models/`

- contains provider-independent normalized application data
- must not depend on source adapters, widgets, or output adapters

`dashboard.py`

- composes the five static dashboard panels
- assigns widgets to panel positions
- does not communicate with external services or devices

`display_state.py`

- fingerprints rendering-relevant state
- reads and writes persistent display-state fingerprints
- treats missing or malformed state as a cache miss
- only stores non-sensitive SHA-256 fingerprints

`design/`

- contains shared visual constants
- contains the common HUD frame
- contains genuinely reusable drawing helpers

`widgets/`

- renders deterministic 128 × 128 Pillow images
- may render multiple frames for native Times Gate animations
- owns widget-specific presentation behavior, including animation timing
- must not perform network requests
- must not access environment variables
- must not communicate with the Times Gate

`sources/`

- retrieves external data
- validates important provider responses
- converts provider-specific data into Novachrono application models

`outputs/delivery.py`

- handles generic static-versus-animation delivery
- performs the current single device-delivery retry
- must remain independent of individual widget domains

`outputs/times_gate.py`

- implements the Times Gate local API adapter
- validates device-specific data
- encodes images
- sends static images and native animations

`preview.py`

- combines individual static panel images into a local preview image

`units.py`

- contains temperature-unit definitions and conversion

`i18n.py`

- contains the project's small UI translation table

`cli.py`

- orchestrates one-shot application commands
- connects configuration, sources, models, widgets, state, and outputs
- must not become a permanently running scheduler

## Current Dashboard

The dashboard contains five independently addressable 128 × 128 panels.

Current assignment:

```text
0 -> placeholder
1 -> current weather
2 -> clock and date
3 -> pokemon go
4 -> placeholder
```

The physical displays are numbered 1 through 5.

The weather widget uses live data from Open-Meteo.

The Pokémon GO widget uses:

- ScrapedDuck for current raid data
- ScrapedDuck artwork URLs
- PokeAPI for best-effort Pokémon name localization

Some weather conditions and multi-boss Pokémon GO states use native Times Gate animations.

## Rendering

Rendering is a core part of Novachrono.

Widget renderers should:

- produce deterministic output for deterministic input
- return exactly 128 × 128 pixel images
- use RGB mode for final panel images
- remain independent of network and device communication
- use the shared Novachrono design where appropriate
- prioritize readability on the physical display
- avoid very small text where possible
- handle variable-width values intentionally

Some widgets may return multiple images representing animation frames.

Animation frame generation belongs to the widget.

Widget-specific frame timing also belongs to the widget because it is part of the intended presentation.

Transport logic and device delivery belong in `outputs/`.

The physical Times Gate display can make small bright pixels bloom.

A layout that looks good in a PNG preview may still require adjustment on the real device.

Treat physical-device results as the final visual authority.

Do not over-generalize layouts.

Widget-specific geometry may remain inside the widget.

## Shared Design

The shared frame is intentionally consistent across widgets.

Shared design code belongs in `design/` only when it is genuinely reusable.

Do not move every coordinate or drawing operation into shared helpers.

Prefer:

```text
shared visual primitive -> design/
widget-specific geometry -> widget module
```

Avoid creating generic layout systems unless multiple widgets clearly need the same behavior.

## Clock

The clock:

- displays current local time
- displays the numeric date
- requires a timezone-aware `datetime`
- uses the shared HUD frame
- renders a single static panel

Clock rendering must remain independent of scheduling and device communication.

`send-clock` intentionally sends every time it is invoked.

Periodic clock updates belong outside the widget renderer and outside a permanently running Python scheduler.

## Weather

Weather values are stored internally in Celsius.

The renderer may display:

```text
C
F
```

Conversion belongs at the presentation boundary.

Layouts must remain usable for:

- negative temperatures
- three-digit Fahrenheit temperatures
- precipitation values up to 100%

Current animated conditions:

```text
RAIN
FOG
```

Rain currently uses:

```text
3 frames
350 ms per frame
```

Fog currently uses:

```text
10 frames
500 ms per frame
```

Other weather conditions currently render as static panels.

Weather change detection is based on rendering-relevant normalized state.

`send-weather` skips Times Gate delivery when the persisted fingerprint matches.

`send-weather --force` bypasses that comparison.

Do not reintroduce forecast fields unless an implemented feature actually needs them.

## Pokémon GO

The Pokémon GO widget currently displays:

- regular five-star raid bosses
- Shadow five-star raid bosses
- Mega raid bosses
- shiny availability
- downloaded boss artwork when available

The UI labels Shadow five-star raids as:

```text
CRYPTO
```

Regular five-star and Shadow five-star bosses share the upper slot.

Regular five-star entries are followed by Shadow five-star entries.

The upper slot uses:

- five cyan sparkle-stars for regular five-star raids
- `CRYPTO` for Shadow five-star raids

Mega raids use the lower slot.

When multiple bosses are active, the renderer produces multiple frames.

The animation length is determined by the longest non-empty category.

Shorter non-empty categories wrap while the longer category continues.

Pokémon GO raid frames currently use a duration of:

```text
10 seconds
```

Artwork and name localization are best-effort.

Failure to download artwork or localize a name should not prevent the widget from rendering usable raid information.

`send-pokemon` compares the raw normalized ScrapedDuck roster before localization and artwork retrieval.

If the persisted fingerprint matches:

- localization is skipped
- artwork retrieval is skipped
- rendering is skipped
- device delivery is skipped

`send-pokemon --force` bypasses change detection.

Do not add unrelated Pokémon GO data unless an implemented widget needs it.

## Display State

Persistent display state lives under:

```text
~/.novachrono/
```

Current files:

```text
weather.state
pokemon-go.state
```

Each file contains one SHA-256 fingerprint.

Keep weather and Pokémon GO state separate.

They are independent one-shot commands and may run in separate processes.

A shared read-modify-write state file would introduce unnecessary coordination and possible lost updates between concurrent processes.

Missing or malformed state is treated as a cache miss.

State must only be updated after successful delivery of the corresponding display.

A state-write failure after successful device delivery should be reported as a warning rather than pretending that device delivery failed.

Do not store raw weather data, Pokémon data, credentials, tokens, or other sensitive values in these files without a concrete requirement.

## Full Synchronization and Recovery

`send-dashboard` is the full synchronization command.

It always sends all five displays regardless of stored fingerprints.

It updates weather and Pokémon GO state only after the corresponding panel has been delivered successfully.

This command is also the manual recovery mechanism if the Times Gate has restarted or lost its displayed state while local fingerprints still exist.

Do not assume that persisted fingerprints prove that the physical device still contains the corresponding image.

Automatic recovery after device restarts remains a deployment concern that has not yet been implemented.

## Internationalization

The current supported locales are:

```text
de_DE
en_US
```

Keep the translation system simple unless requirements justify a more advanced localization library.

Do not add a dependency solely to translate a small number of static strings.

PokeAPI name localization is separate from the internal UI translation table.

## Time

Use timezone-aware `datetime` values.

User-facing times must respect the configured timezone.

Do not mix naive and timezone-aware datetime objects.

Time-dependent behavior should be testable using explicit or injected timestamps where practical.

## External Data Sources

External data sources must remain separate from widget rendering.

Current external sources are:

```text
Open-Meteo
ScrapedDuck
PokeAPI
Pokémon artwork URLs supplied by ScrapedDuck
```

Data-source code should:

- use explicit timeouts
- validate important response data
- provide actionable errors
- avoid logging secrets
- be testable without real network access
- convert provider-specific responses into internal application models

Prefer documented APIs or feeds over scraping where practical.

Do not couple renderer code directly to raw provider responses.

Do not introduce a generic HTTP client solely because several source modules use `urllib`.

Small independent adapters are currently preferred.

Source retrieval currently has no automatic retry.

Do not add source retry behavior without a demonstrated requirement.

## Times Gate

Treat the Times Gate as an external adapter.

The adapter should:

- use explicit timeouts
- validate panel indices
- validate image dimensions
- provide useful errors
- avoid exposing device tokens
- remain independent of widget rendering

The Times Gate adapter currently supports:

- static image delivery
- native multi-frame animation delivery

Native animations should use the Times Gate animation mechanism rather than repeated Python-side uploads.

Generic delivery currently retries one failed Times Gate delivery once after five seconds.

Keep that behavior simple.

Do not introduce:

- retry frameworks
- background workers
- transport abstractions
- connection pools
- fallback loops
- generic resilience frameworks

unless there is a demonstrated requirement.

## Scheduling and Deployment

Novachrono commands are intentionally one-shot operations.

Do not add a permanently running application scheduler merely to update the clock, weather, or Pokémon GO widgets.

The intended Raspberry Pi deployment uses external scheduling, preferably systemd services and timers.

Target schedule:

```text
clock    -> every minute
weather  -> :00 / :15 / :30 / :45
pokemon  -> every full hour
```

At full hours, several commands may become eligible simultaneously.

Their Times Gate transfers must be serialized at deployment level so independent processes do not upload to the device concurrently.

A shared deployment-level lock such as `flock` is preferred over adding scheduler coordination to the Python application.

State-file concurrency does not require a shared lock because weather and Pokémon GO use separate state files.

A full `send-dashboard` synchronization after boot is expected to be part of the deployment design.

Do not implement these deployment details until the relevant Raspberry Pi/systemd work is requested.

## Configuration

Configuration is loaded centrally.

Do not scatter `os.environ` access throughout the project.

Current configuration includes:

```text
NOVACHRONO_LOCALE
NOVACHRONO_TIMEZONE
NOVACHRONO_TEMPERATURE_UNIT
NOVACHRONO_WEATHER_LATITUDE
NOVACHRONO_WEATHER_LONGITUDE
NOVACHRONO_TIMES_GATE_HOST
NOVACHRONO_TIMES_GATE_TOKEN
```

Process environment variables override `.env`.

Weather latitude and longitude must be configured together.

Never commit:

- real Times Gate tokens
- API keys
- private feed URLs
- personal credentials
- `.env`

Update `.env.example` whenever public configuration changes.

## Dependencies

Keep dependencies intentional.

Before adding one, ask:

- Is the standard library sufficient?
- Is the dependency necessary?
- Is it maintained?
- Does it work on the intended Raspberry Pi environment?
- Is the additional supply-chain risk justified?

Do not add frameworks to replace small amounts of straightforward Python.

Current runtime dependencies are intentionally small.

## Tests

Behavior changes should normally include tests.

Tests should be:

- fast
- deterministic
- readable
- independent of real external services
- independent of a physical Times Gate
- independent of the current local timezone or date

Prefer behavioral rendering tests over large golden-image snapshots.

Small targeted pixel assertions are acceptable when protecting a specific visual invariant or regression.

Avoid tests that merely freeze arbitrary implementation details such as incidental coordinates.

Test public behavior through public APIs where practical.

Private helpers normally do not need separate tests when their behavior is already covered through a public entry point.

When production behavior changes, remove or update tests that only describe obsolete behavior.

Do not preserve meaningless tests purely to maintain a test count.

Current local checks are:

```shell
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run bandit -r src
uv run pip-audit
```

A pip-audit skip entry for the local unpublished `novachrono` package is expected.

Hardware-related changes should additionally be smoke-tested on a Times Gate when possible:

```shell
uv run novachrono send-dashboard
uv run novachrono send-weather
uv run novachrono send-pokemon
uv run novachrono send-clock
uv run novachrono send-weather --force
uv run novachrono send-pokemon --force
```

## Formatting and Linting

Ruff is the formatter and linter.

Prefer letting Ruff decide ordinary code formatting instead of manually spreading simple expressions over unnecessary lines.

Do not use unusual formatting merely to make code look more explicit.

Before completing a code change, run:

```shell
uv run ruff format .
uv run ruff check .
```

Do not use unsafe automatic fixes unless the change has been reviewed and is clearly appropriate.

## Code Changes

When modifying code:

- keep changes focused
- preserve existing behavior unless intentionally changing it
- avoid unrelated formatting changes
- update tests when behavior changes
- update documentation when configuration or user-facing behavior changes
- avoid hard-coded personal paths, IP addresses, and credentials
- keep public APIs stable unless a breaking change is justified

Prefer deleting dead or unnecessary code over creating abstractions around it.

Do not refactor working code solely because another architectural pattern exists.

For large changes, propose a short implementation plan first.

## Simplicity Guidelines

Before introducing an abstraction, ask whether it solves a current problem.

Examples of abstractions that are currently unnecessary unless requirements change:

- generic widget base classes
- widget registries
- service layers
- repository layers
- dependency-injection frameworks
- generic HTTP clients
- transport interfaces
- theme objects or theme class hierarchies
- generic animation classes
- plugin systems
- event buses
- internal scheduler frameworks

Duplication is acceptable when removing it would create a more complicated dependency structure.

DRY is a guideline, not a requirement to merge unrelated concepts.

## Reviews

When reviewing the repository:

- do not modify files unless asked
- prioritize findings by impact
- distinguish facts from assumptions
- give concrete evidence
- avoid dogmatic recommendations
- consider the constraints of a Raspberry Pi and a small hobby project
- call out obsolete tests when behavior has changed
- avoid recommending architecture that is disproportionate to the project

Suggested priorities:

```text
P0 - critical correctness or security issue
P1 - important reliability or maintainability issue
P2 - useful improvement with clear benefit
P3 - optional or cosmetic improvement
```

## Assets and Licensing

Do not assume that artwork, fonts, icons, sprites, logos, or other assets found online may be redistributed.

Prefer:

- original assets
- programmatically drawn assets
- openly licensed assets with documented attribution

Do not commit proprietary or unlicensed third-party assets.

Remote artwork used at runtime should not automatically be added to the repository.

## Documentation

Keep documentation aligned with implemented behavior.

When behavior changes, check whether the following need updates:

```text
README.md
.env.example
AGENTS.md
CONTRIBUTING.md
CITATION.cff
```

Do not document planned features as if they already exist.

Clearly distinguish implemented behavior from roadmap items.

Examples and CLI commands should reflect actual current behavior.

## Guiding Principle

The best solution for Novachrono is usually the simplest solution that is correct, secure, readable, testable, and easy to maintain.
