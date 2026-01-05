"""Tests for Node-RED button entity."""

from unittest.mock import MagicMock

import pytest

from custom_components.nodered.button import NodeRedButton
from custom_components.nodered.const import CONF_CONFIG, CONF_NODE_ID, CONF_SERVER_ID
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


@pytest.mark.asyncio
async def test_button_press_sends_event(
    hass: HomeAssistant,
    fake_connection: FakeConnection,
) -> None:
    """Button.press should send an automation_triggered event with the entity state."""
    config = {CONF_ID: "m-1", CONF_SERVER_ID: "s1", CONF_NODE_ID: "n1", CONF_CONFIG: {}}
    node = NodeRedButton(hass, config, fake_connection)

    # Set entity id and an HA state for it
    node.entity_id = "button.test"
    hass.states.async_set(node.entity_id, "ok")

    node.press()

    # Verify last sent event via the convenience property
    assert fake_connection.sent is not None, "No message sent"
    last = fake_connection.sent
    assert last["type"] == "event"
    # When using the real hass, states.get returns a State object
    assert last["event"]["data"]["entity"].state == "ok"
    assert last["event"]["data"] is not None


@pytest.mark.asyncio
async def test_button_async_press_calls_press(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """Async press should delegate to press() and initial state is None."""
    config = {CONF_ID: "m-2", CONF_SERVER_ID: "s2", CONF_NODE_ID: "n2", CONF_CONFIG: {}}
    node = NodeRedButton(hass, config, fake_connection)

    # initial state should be None
    assert node.state is None

    # async_press should call press
    node.press = MagicMock()
    await node.async_press()
    assert node.press.called
