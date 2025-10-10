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

- **Linting and Formatting:**
  - Run `scripts/lint` to apply `flake8`, `isort`, and `black` checks.

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
