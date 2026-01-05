"""Tests for Node-RED select entity."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered import select
from custom_components.nodered.const import DOMAIN
from custom_components.nodered.select import NodeRedSelect
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


@pytest.mark.asyncio
async def test_async_select_option_sends_message(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """async_select_option should send an event message with the selected option."""
    connection = fake_connection
    config = {
        select.CONF_ID: "test-msg-id",
        "server_id": "s1",
        "node_id": "n1",
        select.CONF_CONFIG: {},
    }
    node = NodeRedSelect(hass, config, connection)

    await node.async_select_option("chosen-option")

    # Verify last sent message via convenience property
    assert connection.sent is not None, "No message sent"
    last = connection.sent
    assert last["type"] == "event"
    # payload keys are under the 'event' object
    payload = last.get("event")
    assert payload[select.CONF_TYPE] == select.EVENT_VALUE_CHANGE
    assert payload[select.CONF_VALUE] == "chosen-option"


def test_update_entity_state_attributes_sets_current_option(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_entity_state_attributes should set _attr_current_option."""
    connection = fake_connection
    config = {
        select.CONF_ID: "id-1",
        "server_id": "s1",
        "node_id": "n1",
        select.CONF_CONFIG: {},
    }
    node = NodeRedSelect(hass, config, connection)

    msg = {select.CONF_STATE: "option-42"}
    node.update_entity_state_attributes(msg)

    assert node._attr_current_option == "option-42"


def test_update_discovery_config_sets_icon_and_options(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_discovery_config should set icon and options from discovery config."""
    connection = fake_connection
    config = {
        select.CONF_ID: "id-2",
        "server_id": "s1",
        "node_id": "n1",
        select.CONF_CONFIG: {},
    }
    node = NodeRedSelect(hass, config, connection)

    discovery = {
        select.CONF_CONFIG: {
            select.CONF_ICON: "mdi:test-icon",
            select.CONF_OPTIONS: ["a", "b", "c"],
        }
    }

    node.update_discovery_config(discovery)

    assert node._attr_icon == "mdi:test-icon"
    assert node._attr_options == ["a", "b", "c"]


def test_update_discovery_config_without_options_or_icon(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_discovery_config should handle missing icon and options gracefully."""
    connection = fake_connection
    config = {
        select.CONF_ID: "id-3",
        "server_id": "s1",
        "node_id": "n1",
        select.CONF_CONFIG: {},
    }
    node = NodeRedSelect(hass, config, connection)

    # Set initial values to verify they don't change
    node._attr_icon = "mdi:initial-icon"
    node._attr_options = ["initial", "options"]

    # Empty config
    discovery = {select.CONF_CONFIG: {}}

    node.update_discovery_config(discovery)

    # Icon should fall back to the SELECT_ICON from const.py
    assert node._attr_icon == select.SELECT_ICON
    # Options should remain unchanged when not specified
    assert node._attr_options == ["initial", "options"]


def test_class_attributes() -> None:
    """Test that the class has correct constant attributes."""
    # These are defined directly on the class
    assert NodeRedSelect._bidirectional is True
    assert NodeRedSelect.component == select.CONF_SELECT


@pytest.mark.asyncio
async def test_async_setup_entry_registers_discovery_listener(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that async_setup_entry enables select entity discovery."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    # Send discovery message for a select entity
    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "select",
            "server_id": "test-server",
            "node_id": "test-select-node",
            "state": "option1",
            "config": {
                "name": "Test Select",
                "options": ["option1", "option2", "option3"],
            },
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    await hass.async_block_till_done()

    # Verify entity was created through discovery
    entity_id = "select.test_select"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "option1"
