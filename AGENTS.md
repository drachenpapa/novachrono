# AGENTS.md

## Purpose

This repository may be maintained with the help of AI coding agents.

Novachrono is a small open-source hobby project that renders a five-screen dashboard for the Divoom Times Gate. It is designed to run locally on a development computer and later on a Raspberry Pi or another always-on device.

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

## Architecture

Novachrono currently separates these concerns:

```text
Configuration
     |
     v
Dashboard / normalized data
     |
     v
Widget renderers
     |
     v
Pillow images
     |
     +--> Local preview
     |
     +--> Times Gate output adapter
```

As external data sources are added, use this conceptual flow:

```text
External source
     |
     v
Source adapter
     |
     v
Normalized application model
     |
     v
Widget renderer
```

This is a guideline, not a requirement to create an interface or class for every layer.

### Responsibilities

`config.py`
- loads and validates application configuration
- centralizes environment-variable access

`dashboard.py`
- composes the five dashboard panels
- assigns widgets to panel positions

`design/`
- contains shared visual constants and reusable drawing primitives

`widgets/`
- renders deterministic 128 × 128 Pillow images
- must not perform network requests
- must not communicate with the Times Gate

`outputs/`
- contains external output adapters
- currently contains the Times Gate adapter

`preview.py`
- combines individual panels into a local preview image

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
3 -> pokémon go
4 -> placeholder
```

The weather widget uses live data from Open-Meteo.

The Pokémon GO panel uses live raid data from ScrapedDuck and artwork from the PokéAPI.

## Rendering

Rendering is a core part of Novachrono.

Widget renderers should:

- produce deterministic output for deterministic input
- return exactly 128 × 128 pixel images
- use RGB mode
- remain independent of network and device communication
- use the shared Novachrono design where appropriate
- prioritize readability on the physical display
- avoid very small text where possible
- handle variable-width values intentionally

The physical Times Gate display can make small bright pixels bloom. A layout that looks good in a PNG preview may still require adjustment on the real device.

Do not over-generalize layouts. Widget-specific geometry may remain inside the widget.

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

Do not reintroduce forecast fields unless an implemented feature actually needs them.

## Internationalization

The current supported locales are:

```text
de_DE
en_US
```

Keep the translation system simple unless requirements justify a more advanced localization library.

Do not add a dependency solely to translate a small number of static strings.

## Time

Use timezone-aware `datetime` values.

User-facing times must respect the configured timezone.

Do not mix naive and timezone-aware datetime objects.

Time-dependent behavior should be testable using explicit or injected timestamps.

## External Data Sources

External data sources must remain separate from widget rendering.

Data-source code should:

- use explicit timeouts
- validate important response data
- provide actionable errors
- avoid logging secrets
- be testable without real network access
- convert provider-specific responses into internal application models

Prefer documented APIs or feeds over scraping where practical.

Do not couple renderer code directly to raw provider responses.

## Times Gate

Treat the Times Gate as an external adapter.

The adapter should:

- use explicit timeouts
- validate panel indices
- validate image dimensions
- provide useful errors
- avoid exposing device tokens
- remain independent of widget rendering

Do not move device communication into widgets or dashboard drawing code.

Future long-running operation should tolerate temporary device outages and recover automatically.

## Configuration

Configuration is loaded centrally.

Do not scatter `os.environ` access throughout the project.

Current configuration includes:

```text
NOVACHRONO_LOCALE
NOVACHRONO_TIMEZONE
NOVACHRONO_TEMPERATURE_UNIT
NOVACHRONO_TIMES_GATE_HOST
NOVACHRONO_TIMES_GATE_TOKEN
```

Process environment variables override `.env`.

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

Current local checks are:

```shell
uv run ruff format --check .
uv run ruff check .
uv run bandit -r src
uv run pip-audit
uv run pytest
uv run novachrono preview
```

## Code Changes

When modifying code:

- keep changes focused
- preserve existing behavior unless intentionally changing it
- avoid unrelated formatting changes
- update tests when behavior changes
- update documentation when configuration or user-facing behavior changes
- avoid hard-coded personal paths, IP addresses, and credentials
- keep public APIs stable unless a breaking change is justified

For large changes, propose a short implementation plan first.

## Reviews

When reviewing the repository:

- do not modify files unless asked
- prioritize findings by impact
- distinguish facts from assumptions
- give concrete evidence
- avoid dogmatic recommendations
- consider the constraints of a Raspberry Pi and a small hobby project

Suggested priorities:

```text
P0 - critical correctness or security issue
P1 - important reliability or maintainability issue
P2 - useful improvement with clear benefit
P3 - optional or cosmetic improvement
```

## Assets and Licensing

Do not assume that artwork, fonts, icons, sprites, or logos found online may be redistributed.

Prefer:

- original assets
- programmatically drawn assets
- openly licensed assets with documented attribution

Do not commit proprietary or unlicensed third-party assets.

## Guiding Principle

The best solution for Novachrono is usually the simplest solution that is correct, secure, readable, testable, and easy to maintain.
