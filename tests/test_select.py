"""Tests for Node-RED select entity."""

from collections.abc import Callable
from typing import Any

import pytest

from custom_components.nodered import select
from custom_components.nodered.select import NodeRedSelect
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


@pytest.mark.asyncio
async def test_async_select_option_sends_message(hass: HomeAssistant) -> None:
    """async_select_option should send an event message with the selected option."""
    connection = FakeConnection()
    config = {
        select.CONF_ID: "test-msg-id",
        "server_id": "s1",
        "node_id": "n1",
        select.CONF_CONFIG: {},
    }
    node = NodeRedSelect(hass, config, connection)

    await node.async_select_option("chosen-option")

    assert connection.sent is not None
    assert connection.sent["type"] == "event"
    # payload keys are under the 'event' object
    payload = connection.sent["event"]
    assert payload[select.CONF_TYPE] == select.EVENT_VALUE_CHANGE
    assert payload[select.CONF_VALUE] == "chosen-option"


def test_update_entity_state_attributes_sets_current_option(
    hass: HomeAssistant,
) -> None:
    """update_entity_state_attributes should set _attr_current_option."""
    connection = FakeConnection()
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


def test_update_discovery_config_sets_icon_and_options(hass: HomeAssistant) -> None:
    """update_discovery_config should set icon and options from discovery config."""
    connection = FakeConnection()
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


def test_update_discovery_config_without_options_or_icon(hass: HomeAssistant) -> None:
    """update_discovery_config should handle missing icon and options gracefully."""
    connection = FakeConnection()
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
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that async_setup_entry registers the proper discovery listener."""
    # Track if dispatcher_connect was called with right parameters
    connect_called = False
    connect_signal = None
    connect_target = None
    unload_callback = None

    def mock_dispatcher_connect(
        _hass: HomeAssistant, signal: str, target: Any
    ) -> Callable[[], None]:
        nonlocal connect_called, connect_signal, connect_target
        connect_called = True
        connect_signal = signal
        connect_target = target
        return lambda: None  # Return a removal function

    # Mock config entry with async_on_unload method
    class MockConfigEntry:
        """Mock config entry."""

        def async_on_unload(self, callback: Callable[[], None]) -> None:
            """Store the unload callback."""
            nonlocal unload_callback
            unload_callback = callback

    # Replace the dispatcher_connect function in the select module
    monkeypatch.setattr(
        select,
        "async_dispatcher_connect",
        mock_dispatcher_connect,
    )

    # Call the setup
    await select.async_setup_entry(hass, MockConfigEntry(), None)  # type: ignore[arg-type]

    # Verify the dispatcher was connected
    assert connect_called
    expected_signal = select.NODERED_DISCOVERY_NEW.format(select.CONF_SELECT)
    assert connect_signal == expected_signal
    assert callable(connect_target)
    assert unload_callback is not None
    assert callable(connect_target)
