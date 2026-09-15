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
     +--> Times Gate output adapter
```

This is a conceptual structure, not a requirement to create an interface or class for every layer.

### Responsibilities

`config.py`

- loads and validates application configuration
- centralizes environment-variable access

`dashboard.py`

- composes the five static dashboard panels
- assigns widgets to panel positions
- does not communicate with external services or devices

`design/`

- contains shared visual constants
- contains the common HUD frame
- contains genuinely reusable drawing helpers

`widgets/`

- renders deterministic 128 × 128 Pillow images
- may render multiple frames for native Times Gate animations
- must not perform network requests
- must not access environment variables
- must not communicate with the Times Gate

`sources/`

- retrieves external data
- validates important provider responses
- converts provider-specific data into Novachrono application models

`outputs/`

- contains external output adapters
- currently contains the Times Gate adapter
- handles static and native multi-frame device delivery

`preview.py`

- combines individual static panel images into a local preview image

`units.py`

- contains temperature-unit definitions and conversion

`i18n.py`

- contains the project's small UI translation table

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

The clock, some weather conditions, and multi-boss Pokémon GO states use native Times Gate animations.

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

Animation timing and device delivery belong outside the widget.

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
- uses a horizontal Horizon-style indicator
- renders multiple frames for a native Times Gate sweep animation

The current clock animation is intentionally simple and calm.

Do not replace native Times Gate animation with a Python-side sleep/update loop without a concrete reason.

Do not make the clock depend on network access or device communication.

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

Other weather conditions currently render as static panels.

Do not reintroduce forecast fields unless an implemented feature actually needs them.

## Pokémon GO

The Pokémon GO widget currently displays:

- regular five-star raid bosses
- Mega raid bosses
- shiny availability
- downloaded boss artwork when available

Shadow raids are intentionally excluded.

When multiple bosses are active, the renderer produces multiple frames.

If the five-star and Mega boss counts differ, the shorter category wraps while the longer category continues.

Artwork and name localization are best-effort.

Failure to download artwork or localize a name should not prevent the widget from rendering usable raid information.

Do not add unrelated Pokémon GO data unless an implemented widget needs it.

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

Time-dependent behavior should be testable using explicit or injected timestamps.

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

Do not add:

- retry frameworks
- background workers
- transport abstractions
- connection pools
- fallback loops

unless there is a demonstrated requirement.

Future long-running operation should tolerate temporary device outages and recover automatically.

That future requirement does not justify implementing retry or scheduling infrastructure prematurely.

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
uv run bandit -r src
uv run pip-audit
uv run pytest
uv run novachrono preview
```

Hardware-related changes should additionally be smoke-tested on a Times Gate when possible:

```shell
uv run novachrono send-clock
uv run novachrono send-dashboard
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
