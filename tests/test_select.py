"""Tests for Node-RED select entity."""

import inspect
import logging
from collections.abc import Callable
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.nodered import select
from custom_components.nodered.const import CONF_SELECT, NODERED_DISCOVERY_NEW
from custom_components.nodered.select import NodeRedSelect


class FakeConnection:
    """Fake connection for testing."""

    def __init__(self) -> None:
        """Initialize fake connection."""
        self.sent = None

    def send_message(self, msg: dict[str, Any]) -> None:
        """Store sent message."""
        self.sent = msg


@pytest.mark.asyncio
async def test_async_select_option_sends_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """async_select_option should send an event message with the selected option."""
    # Monkeypatch NodeRedEntity.__init__ to avoid parent init behavior
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda _self, _hass, _config: None
    )
    # Monkeypatch event_message to return the payload so we can assert easily
    monkeypatch.setattr(
        select,
        "event_message",
        lambda message_id, payload: {"message_id": message_id, **payload},
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "test-msg-id"}
    node = NodeRedSelect(None, config, connection)

    await node.async_select_option("chosen-option")

    assert connection.sent is not None
    # Expect the payload contains the message id and the value/type keys
    assert connection.sent.get("message_id") == "test-msg-id"
    assert connection.sent.get(select.CONF_TYPE) == select.EVENT_VALUE_CHANGE
    # CONF_VALUE was imported into the select module
    assert connection.sent.get(select.CONF_VALUE) == "chosen-option"


def test_update_entity_state_attributes_sets_current_option(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_entity_state_attributes should set _attr_current_option."""
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda _self, _hass, _config: None
    )
    # Ensure parent update_entity_state_attributes does not run
    monkeypatch.setattr(
        select.NodeRedEntity,
        "update_entity_state_attributes",
        lambda _self, _msg: None,
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "id-1"}
    node = NodeRedSelect(None, config, connection)

    msg = {select.CONF_STATE: "option-42"}
    node.update_entity_state_attributes(msg)

    assert node._attr_current_option == "option-42"


def test_update_discovery_config_sets_icon_and_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_discovery_config should set icon and options from discovery config."""
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda _self, _hass, _config: None
    )
    # Ensure parent update_discovery_config does not run
    monkeypatch.setattr(
        select.NodeRedEntity, "update_discovery_config", lambda _self, _msg: None
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "id-2"}
    node = NodeRedSelect(None, config, connection)

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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_discovery_config should handle missing icon and options gracefully."""
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda _self, _hass, _config: None
    )
    # Ensure parent update_discovery_config does not run
    monkeypatch.setattr(
        select.NodeRedEntity, "update_discovery_config", lambda _self, _msg: None
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "id-3"}
    node = NodeRedSelect(None, config, connection)

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
    assert NodeRedSelect._component == select.CONF_SELECT


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
    await select.async_setup_entry(hass, MockConfigEntry(), None)

    # Verify the dispatcher was connected
    if not connect_called:
        pytest.fail("Dispatcher connect was not called")
    expected_signal = select.NODERED_DISCOVERY_NEW.format(select.CONF_SELECT)
    if connect_signal != expected_signal:
        pytest.fail(f"Wrong signal: {connect_signal}, expected: {expected_signal}")
    if not callable(connect_target):
        pytest.fail("Target is not callable")
    if unload_callback is None:
        pytest.fail("Unload callback was not registered")
    assert callable(connect_target)


async def _async_setup_entity(
    hass: Any, config: dict[str, Any], async_add_entities: Any, connection: Any
) -> None:
    """Set up a NodeRedSelect entity from discovery."""
    entity = NodeRedSelect(hass, config, connection)
    try:
        await async_add_entities([entity])
    except Exception:
        # If add_entities raises, log the error for debugging
        logging.getLogger(__name__).exception("Failed to add entities")


async def async_setup_entry(hass: Any, _entry: Any, async_add_entities: Any) -> bool:
    """Register discovery listener for Node-RED select entities."""
    signal = f"{NODERED_DISCOVERY_NEW}.{CONF_SELECT}"

    async def _discovered(config: dict[str, Any], connection: Any) -> None:
        await _async_setup_entity(hass, config, async_add_entities, connection)

    result = async_dispatcher_connect(hass, signal, _discovered)
    if inspect.isawaitable(result):
        await result
    return True
