"""Tests for discovery logic."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator
import voluptuous as vol

from custom_components.nodered.const import (
    CONF_COMPONENT,
    CONF_NODE_ID,
    CONF_REMOVE,
    CONF_SENSOR,
    CONF_SERVER_ID,
    DOMAIN,
    DOMAIN_DATA,
)
from custom_components.nodered.discovery import (
    ALREADY_DISCOVERED,
    async_discover,
    async_register_entity,
    async_register_platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

SENSOR_MSG = {CONF_COMPONENT: CONF_SENSOR, CONF_SERVER_ID: "srv", CONF_NODE_ID: "node"}
SENSOR_HASH = "nodered-srv-node"


def _fake_entity(unique_id: str) -> MagicMock:
    entity = MagicMock()
    entity.unique_id = unique_id
    entity.entity_id = "sensor.fake"
    return entity


async def test_discover_new_calls_platform(hass: HomeAssistant) -> None:
    """A new node's discovery creates the entity through its platform."""
    hass.data[DOMAIN_DATA] = {}
    created: list[tuple[dict[str, Any], Any]] = []
    async_register_platform(
        hass, CONF_SENSOR, lambda msg, conn: created.append((msg, conn))
    )
    connection = object()

    async_discover(hass, SENSOR_MSG, connection)  # type: ignore[arg-type]

    assert created == [(SENSOR_MSG, connection)]
    assert SENSOR_HASH in hass.data[DOMAIN_DATA][ALREADY_DISCOVERED]


async def test_discover_existing_updates_entity(hass: HomeAssistant) -> None:
    """A discovered node's discovery updates its entity, including removal."""
    hass.data[DOMAIN_DATA] = {ALREADY_DISCOVERED: {SENSOR_HASH}}
    entity = _fake_entity(SENSOR_HASH)
    async_register_entity(hass, entity)
    connection = object()

    async_discover(hass, SENSOR_MSG, connection)  # type: ignore[arg-type]
    remove_msg = {**SENSOR_MSG, CONF_REMOVE: True}
    async_discover(hass, remove_msg, connection)  # type: ignore[arg-type]

    assert entity.handle_discovery_update.call_args_list == [
        ((SENSOR_MSG, connection),),
        ((remove_msg, connection),),
    ]


async def test_discover_ignores_unsupported_component(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Unsupported components are ignored and logged."""
    hass.data[DOMAIN_DATA] = {}
    platform = MagicMock()
    async_register_platform(hass, CONF_SENSOR, platform)

    async_discover(hass, {**SENSOR_MSG, CONF_COMPONENT: "unsupported"}, object())  # type: ignore[arg-type]

    platform.assert_not_called()
    assert "not supported" in caplog.text


async def test_discover_raises_when_not_loaded(hass: HomeAssistant) -> None:
    """Discovery raises while the integration is not loaded."""
    with pytest.raises(HomeAssistantError, match="integration is not loaded"):
        async_discover(hass, SENSOR_MSG, object())  # type: ignore[arg-type]

    assert DOMAIN_DATA not in hass.data


async def test_discover_raises_for_unloaded_platform(hass: HomeAssistant) -> None:
    """Discovery for an unloaded platform raises and creates nothing."""
    hass.data[DOMAIN_DATA] = {}
    platform = MagicMock()
    unregister = async_register_platform(hass, CONF_SENSOR, platform)

    unregister()
    with pytest.raises(HomeAssistantError, match="sensor platform is not loaded"):
        async_discover(hass, SENSOR_MSG, object())  # type: ignore[arg-type]

    platform.assert_not_called()
    assert SENSOR_HASH not in hass.data[DOMAIN_DATA][ALREADY_DISCOVERED]


async def test_discover_platform_error_is_raised(hass: HomeAssistant) -> None:
    """An error creating the entity is raised and the node isn't marked discovered."""
    hass.data[DOMAIN_DATA] = {}
    async_register_platform(
        hass, CONF_SENSOR, MagicMock(side_effect=vol.Invalid("bad state"))
    )

    with pytest.raises(vol.Invalid, match="bad state"):
        async_discover(hass, SENSOR_MSG, object())  # type: ignore[arg-type]

    assert SENSOR_HASH not in hass.data[DOMAIN_DATA][ALREADY_DISCOVERED]


async def test_rediscovery_and_config_update_reach_entity(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Rediscovery and config updates over the websocket update the entity."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    discovery = {
        "type": "nodered/discovery",
        "component": "sensor",
        "server_id": "s1",
        "node_id": "n1",
        "state": "on",
        "config": {"name": "First"},
    }

    await client.send_json({"id": 1, **discovery})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    state = hass.states.get("sensor.first")
    assert state is not None

    await client.send_json({"id": 2, **discovery, "config": {"name": "Second"}})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    state = hass.states.get("sensor.first")
    assert state is not None
    assert state.attributes["friendly_name"] == "Second"

    await client.send_json(
        {
            "id": 3,
            "type": "nodered/entity/update_config",
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Third"},
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    state = hass.states.get("sensor.first")
    assert state is not None
    assert state.attributes["friendly_name"] == "Third"


async def test_discovery_with_invalid_state_is_rejected(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A discovery state HA would reject is returned as an error, then retried."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    discovery = {
        "type": "nodered/discovery",
        "component": "sensor",
        "server_id": "s1",
        "node_id": "n1",
        "config": {"name": "Temp", "unit_of_measurement": "°C"},
    }

    await client.send_json({"id": 1, **discovery, "state": "not a number"})
    resp = await client.receive_json()
    await hass.async_block_till_done()

    assert not resp["success"]
    assert resp["error"]["code"] == "invalid_format"
    assert "non-numeric value" in resp["error"]["message"]
    assert hass.states.get("sensor.temp") is None

    await client.send_json({"id": 2, **discovery, "state": 21.5})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.temp")
    assert state is not None
    assert state.state == "21.5"
