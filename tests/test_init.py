"""Test nodered setup process."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Relative imports for the module under test and helpers
import custom_components.nodered as nodered_mod
from custom_components.nodered import (
    DOMAIN_DATA,
    PLATFORMS_LOADED,
    async_remove_config_entry_device,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.nodered.const import CONF_VERSION, DOMAIN
from custom_components.nodered.entity import NodeRedEntity, generate_device_identifiers
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er


class DummyEntity(NodeRedEntity):  # noqa: D101
    component = "sensor"


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
async def test_setup_unload_and_reload_entry(
    hass: HomeAssistant, enable_custom_integrations: Any
) -> None:
    """Test entry setup, reload, and unload using HA lifecycle."""
    _ = enable_custom_integrations
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)

    # Simulate Home Assistant setup lifecycle
    setup_result = await hass.config_entries.async_setup(config_entry.entry_id)
    assert setup_result
    assert config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN_DATA in hass.data

    # Simulate reload
    result = await hass.config_entries.async_reload(config_entry.entry_id)
    assert result is True
    assert config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN_DATA in hass.data

    # Simulate unload
    result = await hass.config_entries.async_unload(config_entry.entry_id)
    assert result
    assert config_entry.state == ConfigEntryState.NOT_LOADED
    assert DOMAIN_DATA not in hass.data


@pytest.mark.asyncio
async def test_async_setup_entry_invokes_start_and_registers(
    monkeypatch: pytest.MonkeyPatch, hass: HomeAssistant
) -> None:
    called: dict[str, Any] = {}

    async def fake_forward(entry: Any, platforms: Any) -> None:
        called["forward"] = (entry, platforms)

    async def fake_start_discovery(_h: HomeAssistant, _dd: dict[str, Any]) -> None:
        called["start_discovery"] = True

    def fake_register(_h: HomeAssistant) -> None:
        called["register"] = True

    hass.config_entries.async_forward_entry_setups = fake_forward  # type: ignore[attr-defined]
    monkeypatch.setattr(nodered_mod, "start_discovery", fake_start_discovery)
    monkeypatch.setattr(nodered_mod, "register_websocket_handlers", fake_register)

    # Dummy entry implementing add_update_listener and async_on_unload
    class DummyEntry:
        def __init__(self) -> None:
            self.entry_id = "e1"
            self._unloads = []

        def add_update_listener(self, _cb: Any) -> Any:
            # mimic real behavior by returning a remove callback
            def remove() -> None:
                self._unloads.append("removed")

            return remove

        def async_on_unload(self, cb: Any) -> None:
            # store for verification
            self._on_unload = cb

    entry = DummyEntry()

    res = await async_setup_entry(hass, entry)  # type: ignore[arg-type]
    assert res is True
    assert "forward" in called
    assert "start_discovery" in called
    assert "register" in called
    # domain data should be present
    assert DOMAIN_DATA in hass.data


@pytest.mark.asyncio
async def test_async_unload_entry_stops_discovery_and_cleans_data(
    monkeypatch: pytest.MonkeyPatch, hass: HomeAssistant
) -> None:
    called: dict[str, bool] = {}
    hass.data[DOMAIN_DATA] = {PLATFORMS_LOADED: {"sensor"}}

    async def fake_unload(_entry: Any, _platform: str) -> bool:
        called["unload_called"] = True
        return True

    hass.config_entries.async_forward_entry_unload = fake_unload  # type: ignore[attr-defined]
    monkeypatch.setattr(
        nodered_mod, "stop_discovery", lambda _h: called.setdefault("stopped", True)
    )

    class DummyEntry:
        entry_id = "e2"

    entry = DummyEntry()
    res = await async_unload_entry(hass, entry)  # type: ignore[arg-type]
    assert res is True
    assert called.get("stopped", False) is True
    assert DOMAIN_DATA not in hass.data


@pytest.mark.asyncio
async def test_async_unload_entry_partial_failure(
    monkeypatch: pytest.MonkeyPatch, hass: HomeAssistant
) -> None:
    """Test unload when some platforms fail to unload."""
    hass.data[DOMAIN_DATA] = {PLATFORMS_LOADED: {"sensor", "switch"}}

    call_count = 0

    async def fake_unload(_entry: Any, platform: str) -> bool:
        nonlocal call_count
        call_count += 1
        # First call succeeds, second fails
        return call_count == 1

    hass.config_entries.async_forward_entry_unload = fake_unload  # type: ignore[attr-defined]

    class DummyEntry:
        entry_id = "e3"

    entry = DummyEntry()
    res = await async_unload_entry(hass, entry)  # type: ignore[arg-type]
    # Should return False when any platform fails
    assert res is False
    # Domain data should remain since unload failed
    assert DOMAIN_DATA in hass.data


@pytest.mark.asyncio
async def test_async_unload_entry_fires_unloaded_event(
    monkeypatch: pytest.MonkeyPatch, hass: HomeAssistant
) -> None:
    """Test unload fires unloaded event on success."""
    hass.data[DOMAIN_DATA] = {PLATFORMS_LOADED: {"sensor"}}
    events_fired = []

    async def fake_unload(_entry: Any, _platform: str) -> bool:
        return True

    async def capture_event(event: Any) -> None:
        events_fired.append(event)

    hass.bus.async_listen(DOMAIN, capture_event)
    hass.config_entries.async_forward_entry_unload = fake_unload  # type: ignore[attr-defined]
    monkeypatch.setattr(nodered_mod, "stop_discovery", lambda _h: None)

    class DummyEntry:
        entry_id = "e4"

    entry = DummyEntry()
    await async_unload_entry(hass, entry)  # type: ignore[arg-type]

    assert len(events_fired) == 1
    assert events_fired[0].data["type"] == "unloaded"


@pytest.mark.asyncio
async def test_async_unload_entry_empty_platforms(
    monkeypatch: pytest.MonkeyPatch, hass: HomeAssistant
) -> None:
    """Test unload with no platforms loaded."""
    hass.data[DOMAIN_DATA] = {}

    called = {"unload": False, "stop": False}

    async def fake_unload(_entry: Any, _platform: str) -> bool:
        called["unload"] = True
        return True

    def fake_stop_discovery(_h: Any) -> None:
        called["stop"] = True

    hass.config_entries.async_forward_entry_unload = fake_unload  # type: ignore[attr-defined]
    monkeypatch.setattr(nodered_mod, "stop_discovery", fake_stop_discovery)

    class DummyEntry:
        entry_id = "e5"

    entry = DummyEntry()
    res = await async_unload_entry(hass, entry)  # type: ignore[arg-type]
    # Should still succeed with empty platforms
    assert res is True
    assert called["stop"] is True
    assert DOMAIN_DATA not in hass.data


@pytest.mark.asyncio
async def test_async_setup_entry_fires_loaded_event_with_version(
    monkeypatch: pytest.MonkeyPatch, hass: HomeAssistant
) -> None:
    """Test setup fires loaded event with correct version."""
    events_fired = []

    async def fake_forward(_entry: Any, _platforms: Any) -> None:
        pass

    async def capture_event(event: Any) -> None:
        events_fired.append(event)

    hass.bus.async_listen(DOMAIN, capture_event)
    hass.config_entries.async_forward_entry_setups = fake_forward  # type: ignore[attr-defined]
    monkeypatch.setattr(nodered_mod, "start_discovery", AsyncMock())
    monkeypatch.setattr(nodered_mod, "register_websocket_handlers", lambda _h: None)

    class DummyEntry:
        def __init__(self) -> None:
            self.entry_id = "e6"

        def add_update_listener(self, _cb: Any) -> Any:
            return lambda: None

        def async_on_unload(self, _cb: Any) -> None:
            pass

    entry = DummyEntry()
    await async_setup_entry(hass, entry)  # type: ignore[arg-type]

    # Verify loaded event was fired
    loaded_events = [e for e in events_fired if e.data.get("type") == "loaded"]
    assert len(loaded_events) == 1
    assert CONF_VERSION in loaded_events[0].data


@pytest.mark.asyncio
async def test_async_remove_config_entry_device_no_entities(
    hass: HomeAssistant,
) -> None:
    """Test device removal when device has no entities."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    identifiers = generate_device_identifiers("device-empty")
    device = device_registry.async_get_or_create(
        identifiers=identifiers,
        config_entry_id=config_entry.entry_id,
    )

    dummy_device = SimpleNamespace(id=device.id)
    res = await async_remove_config_entry_device(hass, dummy_device)  # type: ignore[arg-type]
    # Should succeed even with no entities
    assert res is True


@pytest.mark.asyncio
async def test_async_remove_config_entry_device_multiple_entities(
    hass: HomeAssistant,
) -> None:
    """Test device removal clears all entities from device."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    identifiers = generate_device_identifiers("device-multi")
    device = device_registry.async_get_or_create(
        identifiers=identifiers,
        config_entry_id=config_entry.entry_id,
    )

    ent_reg = er.async_get(hass)
    # Create multiple entities linked to device
    entity1 = ent_reg.async_get_or_create(
        "sensor", "nodered", "u-id-1", device_id=device.id, suggested_object_id="e1"
    )
    entity2 = ent_reg.async_get_or_create(
        "switch", "nodered", "u-id-2", device_id=device.id, suggested_object_id="e2"
    )
    entity3 = ent_reg.async_get_or_create(
        "binary_sensor",
        "nodered",
        "u-id-3",
        device_id=device.id,
        suggested_object_id="e3",
    )

    assert entity1.device_id == device.id
    assert entity2.device_id == device.id
    assert entity3.device_id == device.id

    dummy_device = SimpleNamespace(id=device.id)
    res = await async_remove_config_entry_device(hass, dummy_device)  # type: ignore[arg-type]
    assert res is True

    # All entities should have device_id cleared
    updated1 = ent_reg.async_get(entity1.entity_id)
    updated2 = ent_reg.async_get(entity2.entity_id)
    updated3 = ent_reg.async_get(entity3.entity_id)
    assert updated1 is not None and updated1.device_id is None
    assert updated2 is not None and updated2.device_id is None
    assert updated3 is not None and updated3.device_id is None
