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
) -> None:
    """Button.press should send an automation_triggered event with the entity state."""
    conn = FakeConnection()
    config = {CONF_ID: "m-1", CONF_SERVER_ID: "s1", CONF_NODE_ID: "n1", CONF_CONFIG: {}}
    node = NodeRedButton(hass, config, conn)

    # Set entity id and an HA state for it
    node.entity_id = "button.test"
    hass.states.async_set(node.entity_id, "ok")

    node.press()

    assert conn.sent["type"] == "event"
    # When using the real hass, states.get returns a State object
    assert conn.sent["event"]["data"]["entity"].state == "ok"
    assert conn.sent["event"]["data"] is not None


@pytest.mark.asyncio
async def test_button_async_press_calls_press(hass: HomeAssistant) -> None:
    """Async press should delegate to press() and initial state is None."""
    conn = FakeConnection()
    config = {CONF_ID: "m-2", CONF_SERVER_ID: "s2", CONF_NODE_ID: "n2", CONF_CONFIG: {}}
    node = NodeRedButton(hass, config, conn)

    # initial state should be None
    assert node.state is None

    # async_press should call press
    node.press = MagicMock()
    await node.async_press()
    assert node.press.called
