"""Test nodered setup process."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

# Relative imports for the module under test and helpers
from custom_components.nodered import (
    DOMAIN_DATA,
    PLATFORMS_LOADED,
    async_remove_config_entry_device,
)
from custom_components.nodered.const import CONF_VERSION, DOMAIN, WEBHOOKS
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
async def test_setup_unload_and_reload_entry(hass: HomeAssistant) -> None:
    """Test entry setup, reload, and unload using HA lifecycle."""
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
    hass: HomeAssistant,
) -> None:
    """Test that async_setup_entry properly initializes the integration."""

    # Setup the integration using a real config entry
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)

    # Set up the integration
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify domain data was initialized
    assert DOMAIN_DATA in hass.data
    # Verify platforms were loaded
    assert PLATFORMS_LOADED in hass.data[DOMAIN_DATA]
    assert len(hass.data[DOMAIN_DATA][PLATFORMS_LOADED]) > 0


@pytest.mark.asyncio
async def test_async_unload_entry_stops_discovery_and_cleans_data(
    hass: HomeAssistant,
) -> None:
    """Test that async_unload_entry properly cleans up."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify data is present
    assert DOMAIN_DATA in hass.data

    # Unload the integration
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify cleanup happened
    assert DOMAIN_DATA not in hass.data


@pytest.mark.asyncio
async def test_async_unload_entry_partial_failure(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
) -> None:
    """Test unload when some platforms fail to unload."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Mock one platform to fail unload
    call_count = 0
    original_unload = hass.config_entries.async_forward_entry_unload

    async def fake_unload(entry: Any, platform: str) -> bool:
        nonlocal call_count
        call_count += 1
        # First call succeeds, second fails
        if call_count == 1:
            return await original_unload(entry, platform)
        return False

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_unload", fake_unload)

    # Try to unload - should fail
    result = await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Should return False when any platform fails
    assert result is False
    # Domain data should remain since unload failed
    assert DOMAIN_DATA in hass.data


@pytest.mark.asyncio
async def test_async_unload_entry_fires_unloaded_event(hass: HomeAssistant) -> None:
    """Test unload fires unloaded event on success."""
    events_fired = []

    async def capture_event(event: Any) -> None:
        events_fired.append(event)

    hass.bus.async_listen(DOMAIN, capture_event)

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Clear events from setup
    events_fired.clear()

    # Unload the integration
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify unloaded event was fired
    unloaded_events = [e for e in events_fired if e.data.get("type") == "unloaded"]
    assert len(unloaded_events) == 1


@pytest.mark.asyncio
async def test_async_unload_entry_empty_platforms(hass: HomeAssistant) -> None:
    """Test unload with no platforms loaded still succeeds."""

    # Setup and immediately unload before any platforms are discovered
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Unload immediately
    result = await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Should still succeed even with no entities/platforms
    assert result is True
    assert DOMAIN_DATA not in hass.data


@pytest.mark.asyncio
async def test_async_setup_entry_fires_loaded_event_with_version(
    hass: HomeAssistant,
) -> None:
    """Test setup fires loaded event with correct version."""
    events_fired = []

    async def capture_event(event: Any) -> None:
        events_fired.append(event)

    hass.bus.async_listen(DOMAIN, capture_event)

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

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


@pytest.mark.asyncio
async def test_webhooks_cleaned_up_on_unload(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that webhooks are cleaned up when integration is unloaded."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Create a websocket client
    client = await hass_ws_client(hass)

    # Register a webhook through the API
    await client.send_json(
        {
            "id": 1,
            "type": "nodered/webhook",
            "server_id": "test-server",
            "name": "test-webhook",
            "webhook_id": "test-webhook-id",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    # Verify webhook was tracked
    assert "test-webhook-id" in hass.data[DOMAIN_DATA][WEBHOOKS]

    # Unload the integration
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify webhooks were cleaned up and domain data was removed
    assert DOMAIN_DATA not in hass.data or WEBHOOKS not in hass.data.get(
        DOMAIN_DATA, {}
    )
