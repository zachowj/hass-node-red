"""Tests for Node-RED text entity."""

from typing import Any

import pytest

from custom_components.nodered import text
from custom_components.nodered.const import CONF_CONFIG
from custom_components.nodered.number import CONF_VALUE
from custom_components.nodered.text import NodeRedText
from homeassistant.components.text import TextExtraStoredData, TextMode
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection

# Test constants to avoid magic numbers in assertions
RESTORED_NATIVE_MAX = 7
RESTORED_NATIVE_MIN = 2
CUSTOM_NATIVE_MIN = 5
CUSTOM_NATIVE_MAX = 50


def test_update_entity_state_coerces_to_string(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """Text entity should coerce incoming state to a string."""
    config: dict[str, Any] = {
        text.CONF_ID: "id-1",
        "server_id": "s1",
        "node_id": "n1",
        "config": {},
    }
    node: NodeRedText = NodeRedText(hass, config, fake_connection)

    # Integer state should be coerced to string
    node.update_entity_state_attributes({text.CONF_STATE: 1765968779435})
    assert node._attr_native_value == "1765968779435"

    # None state should result in None native value
    node.update_entity_state_attributes({text.CONF_STATE: None})
    assert node._attr_native_value is None

    # String state should remain unchanged
    node.update_entity_state_attributes({text.CONF_STATE: "hello"})
    assert node._attr_native_value == "hello"


@pytest.mark.asyncio
async def test_async_set_value_sends_event_message(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """async_set_value should send correct websocket event message."""
    config: dict[str, Any] = {
        text.CONF_ID: "id-send",
        "server_id": "s1",
        "node_id": "n1",
        "config": {},
    }
    node: NodeRedText = NodeRedText(hass, config, fake_connection)

    captured: dict[str, Any] = {}

    def fake_send_message(msg: dict[str, Any]) -> None:
        captured["msg"] = msg

    fake_connection.send_message = fake_send_message
    await node.async_set_value("new-value")

    message_id: Any = "id-send"
    expected: dict[str, Any] = event_message(
        message_id,
        {text.CONF_TYPE: text.EVENT_VALUE_CHANGE, CONF_VALUE: "new-value"},
    )
    assert captured["msg"] == expected


@pytest.mark.asyncio
async def test_async_added_to_hass_restores_native_values_when_available(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """async_added_to_hass should restore native values when last data exists."""
    config: dict[str, Any] = {
        text.CONF_ID: "id-restore",
        "server_id": "s1",
        "node_id": "n1",
        "config": {},
    }
    node: NodeRedText = NodeRedText(hass, config, fake_connection)

    async def fake_get_last_text_data() -> TextExtraStoredData:
        return TextExtraStoredData(
            native_value="restored",
            native_min=RESTORED_NATIVE_MIN,
            native_max=RESTORED_NATIVE_MAX,
        )

    node.async_get_last_text_data = fake_get_last_text_data
    await node.async_added_to_hass()

    assert node._attr_native_max == RESTORED_NATIVE_MAX
    assert node._attr_native_min == RESTORED_NATIVE_MIN
    assert node._attr_native_value == "restored"


@pytest.mark.asyncio
async def test_async_added_to_hass_handles_none_gracefully(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """async_added_to_hass should handle no last data without raising."""
    config: dict[str, Any] = {
        text.CONF_ID: "id-no-restore",
        "server_id": "s1",
        "node_id": "n1",
        "config": {},
    }
    node: NodeRedText = NodeRedText(hass, config, fake_connection)

    async def fake_get_last_text_data() -> None:
        return None

    node.async_get_last_text_data = fake_get_last_text_data
    # Should not raise
    await node.async_added_to_hass()


def test_update_discovery_config_applies_defaults(
    hass: HomeAssistant,
    fake_connection: FakeConnection,
) -> None:
    """update_discovery_config should set default discovery values when not provided."""
    config: dict[str, Any] = {
        text.CONF_ID: "id-defaults",
        "server_id": "s1",
        "node_id": "n1",
        "config": {},  # empty inner config to trigger defaults
    }
    node: NodeRedText = NodeRedText(hass, config, fake_connection)
    node.update_discovery_config({CONF_CONFIG: {}})

    assert node._attr_icon == text.TEXT_ICON
    assert node._attr_native_min == text.DEFAULT_MIN_LENGTH
    assert node._attr_native_max == text.DEFAULT_MAX_LENGTH
    assert node._attr_pattern is None
    assert isinstance(node._attr_mode, TextMode)
    assert node._attr_mode.value == text.DEFAULT_MODE


def test_update_discovery_config_applies_custom_values(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_discovery_config should read and apply configuration values."""
    custom_cfg: dict[str, Any] = {
        text.CONF_ID: "id-custom",
        "server_id": "s1",
        "node_id": "n1",
        "config": {
            text.CONF_ICON: "mdi:test-icon",
            text.CONF_MIN_LENGTH: 5,
            text.CONF_MAX_LENGTH: 50,
            text.CONF_PATTERN: r"^\w+$",
            text.CONF_MODE: "password",
        },
    }
    node: NodeRedText = NodeRedText(hass, custom_cfg, fake_connection)
    node.update_discovery_config({CONF_CONFIG: custom_cfg["config"]})

    assert node._attr_icon == "mdi:test-icon"
    assert node._attr_native_min == CUSTOM_NATIVE_MIN
    assert node._attr_native_max == CUSTOM_NATIVE_MAX
    assert node._attr_pattern == r"^\w+$"
    assert isinstance(node._attr_mode, TextMode)
    assert node._attr_mode.value == "password"
