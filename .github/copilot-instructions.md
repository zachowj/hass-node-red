# Node-RED Companion – AI Guide

## Architecture Overview

- **Integration Structure:**

  - The custom integration resides in `custom_components/nodered`.
  - `manifest.json` defines dependencies (`conversation`, `mqtt`) and exposes a single config entry.
  - `__init__.py` initializes discovery (`start_discovery`), registers websocket handlers, and fires lifecycle events.
  - Entity platforms (e.g., `binary_sensor.py`, `button.py`) dynamically create/update entities based on dispatcher signals.

- **Discovery and Communication:**

  - Node-RED communicates with Home Assistant via websockets (`websocket.py`).
  - Discovery messages are brokered by `discovery.py`, which tracks entities using `ALREADY_DISCOVERED` hashes.
  - Dispatcher signals (`NODERED_DISCOVERY`, `NODERED_CONFIG_UPDATE`) manage entity creation, updates, and removal.

- **Entity Implementation:**
  - All entities inherit from `NodeRedEntity`, which handles lifecycle management, dispatcher subscriptions, and state syncing.
  - Bidirectional entities (e.g., `button`, `switch`) use `_bidirectional = True` to enable HA-to-Node-RED communication.

## Developer Workflows

- **Setup:**

  - Run `scripts/setup` to install dependencies and register pre-commit hooks.
  - Use `scripts/dev` to launch Home Assistant with the integration mounted via `PYTHONPATH`.

- **Testing:**

  - Execute tests with `scripts/test` (wraps `pytest` with coverage).
  - For specific tests: `pytest tests/<file>.py -k <test>`.
  - When writing tests, follow Home Assistant testing best practices and use the
    `pytest-homeassistant-custom-component` package to leverage HA fixtures and helpers.
  - **Avoid inline imports in tests.** Prefer module-level imports at the top of test files; inline imports inside test functions can hide issues from linters, introduce unintended side effects, and make tests harder to read. If a lazy import is required, add a short comment explaining why.
  - **Keep imports at top level in production code.** Prefer module-level imports at the top of Python files for runtime code to avoid obscuring dependency relationships and surprising side-effects; use type-checking blocks (`if TYPE_CHECKING:`) for imports needed only for typing where necessary.

  ## Typing & Type Hints 🔧

  - **Use type hints for public APIs and tests.** Annotate function/method parameters and return types to improve readability and enable static checks.
  - **Annotate `__init__` as returning `None`.** Example: `def __init__(self, x: int) -> None:`.
  - **Prefer built-in generics (Python 3.9+).** Use `list[str]`, `dict[str, Any]` instead of `List[str]` from `typing` when possible.
  - **Use `collections.abc` for callables and ABCs.** For example: `from collections.abc import Callable`.
  - **In tests, annotate fixtures and helper objects.** Example: `def test_example(hass: HomeAssistant) -> None:` and annotate helper classes used in tests to avoid linter warnings.
  - **Use `Any` for heavy/deferred imports.** When importing types would introduce runtime overhead or circular deps, prefer `Any` and add a short comment.
  - **Consider `from __future__ import annotations` for forward refs.** This keeps runtime overhead low and simplifies typing of nested classes.

  These practices help keep the test suite and integration code clearer, reduce false positives from linters, and make type-based refactors easier.

- **Linting and Formatting:**
  - Run `scripts/lint` to run the new pre-commit checks (see `.pre-commit-config.yaml` for details).

## Project-Specific Conventions

- **Entity Discovery:**

  - Use consistent discovery signatures (`config`, `connection`) in `async_setup_entry`.
  - Update `SUPPORTED_COMPONENTS` in `discovery.py` when adding new platforms.

- **Websocket Commands:**

  - Validate commands against schemas in `websocket.py`.
  - Ensure structured responses (`result_message`, `error_message`).

- **Dynamic Configuration:**
  - Use `NODERED_CONFIG_UPDATE` for non-disruptive updates (e.g., name, icon).
  - Sync device registry via `NodeRedEntity.update_discovery_device_info`.

## Key Files and Directories

- `custom_components/nodered/`: Core integration code.
- `tests/`: Test suite leveraging `pytest_homeassistant_custom_component`.
- `scripts/`: Developer utilities for setup, testing, and linting.
- `config/`: Example Home Assistant configuration files.

## External Dependencies

- Requires `node-red-contrib-home-assistant-websocket` (v0.57+) and Home Assistant (2024.5+).
- HACS metadata (`hacs.json`, `info.md`) supports distribution.

## Extending the Integration

- Follow existing patterns in `NodeRedEntity` for new entity types.
- Ensure dispatcher registrations return removal callbacks for cleanup.
- Maintain compatibility with Home Assistant versions by using conditional imports (e.g., `sentence.py`).
- When creating a new entity subclass, set the `component` class attribute to the Home Assistant
  component constant (for example `CONF_SENSOR`, `CONF_SWITCH`). The repository enforces at runtime
  that subclasses define `component` and will raise a `TypeError` if it is missing — this helps
  catch errors early during development.
