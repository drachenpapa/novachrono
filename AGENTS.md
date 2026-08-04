# AGENTS.md

## Purpose

This repository is intended to be maintained with the help of AI coding agents such as GitHub Copilot.

Novachrono is a small open-source hobby project that renders a consistent five-screen dashboard for the Divoom Times Gate. It is expected to run locally, initially on a development computer and later on a Raspberry Pi or another always-on device in the same network as the display.

Agents must prioritize correctness, security, simplicity, readability, maintainability, and testability. The codebase should remain easy to understand for a human maintainer.

Prefer pragmatic solutions over unnecessary abstraction. Do not design for hypothetical enterprise scale.

## General Principles

Follow these priorities:

1. Correctness
2. Security
3. Simplicity
4. Readability
5. Maintainability
6. Testability
7. Performance where relevant

Guidelines:

* Prefer KISS over cleverness.
* Apply DRY with judgment.
* Follow SOLID where it improves clarity.
* Prefer explicit code over implicit magic.
* Prefer composition over inheritance.
* Prefer standard library features over new dependencies when practical.
* Avoid premature optimization.
* Avoid speculative architecture.
* Avoid large rewrites unless explicitly requested.
* Do not introduce abstractions before a concrete need exists.
* Keep the project appropriate for a small self-hosted application.

## Project Context

Before making recommendations or changes, inspect:

* `README.md`
* build and package configuration
* CI configuration
* tests
* relevant source files
* configuration examples
* `.github/copilot/architecture.md`, if present
* `.github/copilot/conventions.md`, if present

Do not infer the architecture from a single file. Understand the surrounding context first.

Do not assume that planned features described in documentation already exist. Distinguish clearly between:

* implemented behavior
* planned behavior
* assumptions
* recommendations

## Project-Specific Principles

Novachrono consists conceptually of four areas:

1. data sources
2. normalized application models
3. widget rendering
4. output adapters

Keep these responsibilities separate where doing so improves readability and testability, but do not create unnecessary layers.

The first implementation target is a static five-panel preview. External data sources and Times Gate communication should be added incrementally.

Important constraints:

* Each Times Gate panel is rendered as a 128 × 128 pixel image.
* The dashboard contains five independently addressable panels.
* Rendering must work without access to a physical Times Gate.
* Every widget should be previewable locally.
* A combined five-panel preview should be available during development.
* External APIs, calendar feeds, and device communication may be unavailable.
* Network failures must not terminate the long-running application.
* Previously valid data may be cached when appropriate.
* Time calculations must use timezone-aware datetime values.
* User-facing times must use the configured local timezone.
* Secrets and local machine configuration must not be committed.
* Treat the Times Gate integration as an external adapter whose behavior may change independently of the application.
* Avoid coupling widget rendering to device communication.
* Avoid coupling rendering code directly to raw external API responses.
* Only transmit a new image when the rendered content has changed, where practical.

## Scope

The repository is responsible for:

* retrieving configured dashboard data
* normalizing external data
* rendering widget images
* producing local previews
* transmitting rendered images to supported displays
* scheduling widget updates
* handling temporary external failures

The repository is not responsible for:

* configuring the user's home network
* providing general NAS or file-server functionality
* managing unrelated Raspberry Pi services
* replacing Home Assistant
* implementing a general-purpose dashboard framework
* distributing unlicensed third-party assets

Do not broaden the project scope without an explicit request.

## Review Rules

When asked to review code or the entire project:

* Do not modify files unless explicitly asked.
* Provide a structured review report.
* Highlight strengths as well as weaknesses.
* Prioritize findings by impact.
* Distinguish facts from assumptions.
* Support recommendations with concrete observations from the codebase.
* Avoid dogmatic advice.
* Do not recommend enterprise patterns for this project unless clearly justified.
* Consider the constraints of a Raspberry Pi or another small always-on device.
* Consider behavior when external services or the Times Gate are unavailable.

Priority scale:

* P0: Critical correctness, security, or data-loss issue
* P1: Important maintainability, architecture, or reliability issue
* P2: Useful improvement with clear benefit
* P3: Optional or cosmetic improvement

For each relevant finding, include:

* Problem
* Evidence
* Impact
* Recommendation
* Estimated effort: S / M / L

## Code Change Rules

When asked to modify code:

* Keep changes small and reviewable.
* Preserve existing behavior unless explicitly asked to change it.
* Avoid unrelated cleanup.
* Avoid broad formatting-only changes.
* Do not introduce new dependencies without a clear reason.
* Update or add tests when behavior changes.
* Keep public APIs stable unless a breaking change is explicitly requested.
* Explain important trade-offs.
* Update documentation when configuration or user-facing behavior changes.
* Do not commit generated previews unless the repository conventions explicitly require them.
* Do not hard-code personal configuration, credentials, IP addresses, account names, or calendar URLs.

Before large changes, propose a short implementation plan.

## Architecture Guidelines

Prefer simple, understandable architecture.

Good architecture means:

* clear responsibilities
* low coupling
* high cohesion
* understandable module boundaries
* minimal global state
* predictable data flow
* testable components
* no unnecessary layers
* graceful handling of unavailable external systems

A likely data flow is:

```text
External source
    |
    v
Source adapter
    |
    v
Normalized model
    |
    v
Widget renderer
    |
    v
Rendered image
    |
    +--> Local preview
    |
    +--> Times Gate output adapter
```

This is a conceptual guide, not a requirement to create one class or interface for every box.

Avoid:

* god classes
* circular dependencies
* over-engineered abstractions
* premature plugin systems
* unnecessary inheritance hierarchies
* hidden side effects
* framework lock-in where avoidable
* direct network requests inside low-level drawing functions
* rendering code that depends on a physical device
* a single global scheduler containing unrelated business logic
* generic frameworks designed for hypothetical future widgets

Add abstractions only when at least one concrete use case benefits from them.

## Data Source Guidelines

External data sources may include HTTP APIs, calendar feeds, or local system information.

Data source code should:

* use explicit timeouts
* handle temporary network failures
* validate important response fields
* avoid logging secrets
* convert raw responses into internal models
* use timezone-aware datetime values
* provide clear error information
* be testable without performing real network requests
* respect service terms and reasonable request intervals

Do not scrape websites when a documented API or feed is available and appropriate.

Do not assume external data is complete, correctly formatted, or always available.

Where useful, distinguish between:

* no data exists
* data is temporarily unavailable
* data is invalid
* authentication failed
* the configured source is disabled

## Rendering Guidelines

Rendering is a core responsibility of Novachrono.

Widget renderers should:

* produce deterministic output for deterministic input
* render at exactly 128 × 128 pixels unless explicitly working on a combined preview
* remain independent of device communication
* avoid performing network requests
* handle missing optional data gracefully
* maintain readable contrast
* avoid text that is too small for the physical display
* use shared design tokens for colors, spacing, and typography
* avoid unnecessary visual inconsistency between widgets
* support local preview generation

Prefer a small shared design system over duplicated literal values.

Examples of shared design values include:

* canvas dimensions
* outer margins
* border radius
* header position
* title font
* primary value font
* footer font
* default background
* default foreground
* accent colors
* icon sizing

Do not over-generalize layouts. Widgets may use different compositions when their content requires it.

When rendering variable-length text:

* define maximum widths
* wrap or truncate intentionally
* avoid silent overflow
* provide sensible fallback text
* test unusually long names and values

## Time and Scheduling Guidelines

Time is central to this project.

Always:

* use timezone-aware datetime values
* avoid mixing naive and aware datetime objects
* store or process timestamps consistently
* convert to the configured timezone at presentation boundaries
* account for daylight-saving transitions
* make time-dependent logic testable using an injected or explicit current time
* avoid calling the system clock throughout business logic

Do not implement minute updates using an uncorrected repeating 60-second sleep when alignment to the minute matters.

Prefer scheduling that aligns clock updates to the beginning of the next minute.

Different widgets may use different update intervals.

Examples:

* clock: every minute
* weather: every 15 to 30 minutes
* calendar or event feed: every 15 minutes or longer
* GitHub metrics: every few minutes
* static information: only when configuration changes

Avoid transmitting unchanged images where practical.

## Times Gate Integration Guidelines

The Times Gate is an external device and must be isolated behind an output adapter.

Device integration should:

* use explicit connection and response timeouts
* handle the device being offline
* avoid terminating the application after a temporary failure
* support updating individual displays
* validate image dimensions and format before transmission
* avoid exposing device tokens in logs
* provide actionable error messages
* permit local rendering without device configuration
* avoid assuming undocumented behavior is permanently stable

The Times Gate integration may rely on unofficial or reverse-engineered behavior. Keep implementation details isolated so they can be updated without changing widget rendering or data source logic.

Do not send all five images when only one display has changed unless the device protocol requires it.

## Configuration Guidelines

Configuration should be explicit and documented.

Use environment variables or configuration files as appropriate, but avoid unnecessary complexity.

Configuration may eventually include:

* local timezone
* Times Gate host
* Times Gate token
* weather location
* weather API key
* GitHub account
* GitHub token
* calendar feed URL
* widget-to-display assignments
* update intervals
* theme settings

Rules:

* provide safe defaults where reasonable
* fail clearly for missing required configuration
* do not commit real secrets
* provide an example configuration
* separate secrets from non-sensitive settings where practical
* validate values near application startup
* do not scatter environment-variable access throughout the codebase
* avoid hard-coded local paths and addresses

## Error Handling and Reliability

Novachrono is expected to run unattended.

Temporary failures should be handled gracefully.

The application should:

* continue running when one data source fails
* avoid replacing valid information with an empty screen after a temporary failure
* preserve the last valid result where appropriate
* log failures with enough context to diagnose them
* avoid excessively repeating identical error messages
* recover automatically when an external service becomes available again
* isolate failures so that one widget does not prevent other widgets from updating

Do not catch exceptions without either handling or logging them meaningfully.

Do not expose tokens, private URLs, or personal data in errors or logs.

## Testing Guidelines

Tests should focus on behavior and important edge cases.

Prefer:

* fast automated tests
* clear test names
* deterministic tests
* meaningful assertions
* tests close to the behavior being verified
* fixed timestamps for time-dependent behavior
* representative rendering inputs
* mocked or fake external adapters at network boundaries
* tests for unavailable and malformed external data

Avoid:

* brittle tests
* excessive mocking
* testing implementation details without benefit
* real external network calls in the default test suite
* dependence on a physical Times Gate
* dependence on the current date or local machine timezone
* slow tests in the default CI path unless necessary

Rendering tests should prefer deterministic inputs and fixed timestamps.

Use visual regression or golden-image tests only when they provide clear value. Do not rely exclusively on large binary image snapshots when smaller behavioral assertions are sufficient.

High-value rendering tests may verify:

* image dimensions
* image mode
* no text overflow for known edge cases
* correct state selection
* correct formatting of values
* fallback behavior for missing data
* stable output for fixed input

If test coverage is weak, recommend high-value tests first.

## Security Guidelines

Check for:

* unsafe input handling
* insecure defaults
* secrets in source code
* weak authentication or authorization patterns
* unsafe deserialization
* command injection risks
* path traversal risks
* dependency risks
* insufficient error handling around external systems
* untrusted remote image or calendar content
* sensitive information in logs

For this project, pay particular attention to:

* GitHub personal access tokens
* weather API keys
* Times Gate device tokens
* calendar feed URLs containing private identifiers
* local configuration files
* downloaded remote assets
* cached API responses
* logs containing event, account, or device information

Never print, generate, commit, or expose secrets.

Do not weaken security controls for convenience.

Do not download and execute remote content.

Validate file paths and remote content before processing them.

## Dependency Guidelines

Keep dependencies intentional.

Before suggesting a new dependency, consider:

* Is the standard library sufficient?
* Is the dependency actively maintained?
* Is it necessary for the project size?
* Does it increase security or supply-chain risk?
* Is the benefit worth the added complexity?
* Does it work reliably on the intended Raspberry Pi environment?
* Is its license compatible with the project?

Prefer small, well-maintained, widely used dependencies.

Do not add a framework merely to avoid writing a small amount of straightforward code.

Pin and update dependencies according to the repository conventions.

GitHub Actions should be pinned to full commit SHAs rather than mutable tags.

## Asset and Licensing Guidelines

Do not assume that images, fonts, logos, sprites, or icons found online may be redistributed.

Before adding an asset, verify:

* its source
* its license
* whether redistribution is permitted
* whether attribution is required
* whether modification is permitted
* whether the license is compatible with the repository

Do not commit:

* official Pokémon artwork without permission
* community artwork without a compatible license
* proprietary fonts
* assets extracted from the Divoom application
* trademarks used in a way that implies endorsement

Prefer:

* original assets
* openly licensed assets
* simple programmatically drawn icons
* assets with documented attribution

Record required attribution in an appropriate file.

## Documentation Guidelines

Documentation should explain intent, constraints, and non-obvious decisions.

Prefer:

* concise README updates
* architecture notes for important decisions
* comments for non-obvious code
* examples for public APIs or configuration
* clear distinction between implemented and planned behavior
* setup instructions that work from a clean environment

Avoid comments that merely repeat the code.

Do not document commands or features that have not been verified.

Update documentation when:

* configuration changes
* setup steps change
* new external services are introduced
* user-visible behavior changes
* architecture decisions affect contributors

## Language-Specific Guidance

Follow established Python best practices once the Python toolchain has been selected.

Consider Python-specific conventions for:

* source layout
* naming
* type annotations
* error handling
* dependency management
* formatting
* linting
* testing
* packaging
* logging

Do not add language-specific tools until the project has chosen them.

Once selected, use the configured project tools rather than introducing competing alternatives.

Avoid mutable default arguments.

Prefer explicit return types for public and non-trivial functions.

Use dataclasses or similarly simple models where they improve clarity. Do not introduce a validation framework unless runtime validation needs justify it.

## Output Style

When reporting findings:

* Be concise but specific.
* Use clear headings.
* Prefer actionable recommendations.
* Separate critical issues from nice-to-have improvements.
* Mention uncertainty explicitly.
* Do not exaggerate minor issues.
* State when a recommendation depends on an unresolved project decision.

For project reviews, use this structure:

1. Executive Summary
2. Strengths
3. Main Risks
4. Architecture Review
5. Code Quality Review
6. Testability Review
7. Security and Dependency Review
8. Prioritized Findings
9. Recommended Next Steps
10. Things Not Worth Changing

## Non-Goals

Do not optimize for:

* academic purity
* unnecessary abstraction
* framework maximalism
* premature scalability
* style-only debates
* large rewrites without strong justification
* hypothetical plugin ecosystems
* enterprise deployment patterns
* maximum configurability before basic functionality exists

The best solution is usually the simplest solution that is correct, secure, readable, reliable, and easy to maintain.
