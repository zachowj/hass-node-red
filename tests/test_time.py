"""Tests for Node-RED time entity."""

from datetime import time as dt_time
import logging
from typing import Any

import pytest

from custom_components.nodered.const import (
    CONF_CONFIG,
    CONF_NODE_ID,
    CONF_SERVER_ID,
    CONF_TIME,
    EVENT_VALUE_CHANGE,
    TIME_ICON,
)
from custom_components.nodered.number import CONF_STATE
from custom_components.nodered.time import (
    CONF_VALUE,
    NodeRedTime,
    _convert_string_to_time,
)
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.const import CONF_ICON, CONF_ID, CONF_TYPE
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


def test_convert_string_to_time_various() -> None:
    """Valid strings and None should convert appropriately."""
    assert _convert_string_to_time("12:34:56") == dt_time(12, 34, 56)
    # Full datetime string with date/time zone should still extract time (tz stripped)
    assert _convert_string_to_time("2023-08-01T09:10:11Z") == dt_time(9, 10, 11)
    # Time string with offset should also return naive time with same clock time
    assert _convert_string_to_time("2023-08-01T09:10:11+02:00") == dt_time(9, 10, 11)
    assert _convert_string_to_time(None) is None


def test_convert_string_with_milliseconds_and_spaces() -> None:
    """Time strings with milliseconds and surrounding whitespace should parse."""
    assert _convert_string_to_time(" 09:10:11.123 ") == dt_time(9, 10, 11, 123000)


def test_convert_string_with_microseconds() -> None:
    """Time strings with microseconds should parse correctly."""
    assert _convert_string_to_time("09:10:11.123456") == dt_time(9, 10, 11, 123456)


def test_convert_non_string_logs_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Non-string inputs should either return None and log, or raise an error.

    Different versions of the parser may raise a TypeError for non-string
    inputs instead of returning None. Accept either behavior while ensuring
    we don't silently succeed.
    """
    caplog.set_level(logging.ERROR)
    try:
        result = _convert_string_to_time(12345)  # type: ignore[arg-type]
    except TypeError:
        # Acceptable: implementation may raise for non-string input
        return
    # Or, if it returned, ensure it returned None and logged the error
    assert result is None
    assert "Unable to parse time" in caplog.text


def test_convert_string_to_time_invalid_logs_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Invalid time strings return None and log an exception."""
    caplog.set_level(logging.ERROR)
    result = _convert_string_to_time("not-a-time")
    assert result is None
    assert "Unable to parse time" in caplog.text


def test_node_red_time_update_state_and_discovery(hass: HomeAssistant) -> None:
    """Updating entity state and discovery config sets attributes correctly."""
    conn = FakeConnection()
    config: dict[str, Any] = {
        CONF_ID: "mid-1",
        CONF_SERVER_ID: "s1",
        CONF_NODE_ID: "n1",
        CONF_CONFIG: {},
    }
    nrt = NodeRedTime(hass, config, conn)

    # Initially no native value
    assert nrt._attr_native_value is None

    # Update state with a time string
    nrt.update_entity_state_attributes({CONF_STATE: "01:02:03"})
    assert nrt._attr_native_value == dt_time(1, 2, 3)

    # Update with None clears/keeps None
    nrt.update_entity_state_attributes({CONF_STATE: None})
    assert nrt._attr_native_value is None

    # Update state with timezone-aware datetime string -> naive time expected
    nrt.update_entity_state_attributes({CONF_STATE: "2023-08-01T09:10:11Z"})
    assert nrt._attr_native_value == dt_time(9, 10, 11)

    # Discovery config without icon uses default TIME_ICON
    nrt.update_discovery_config({CONF_CONFIG: {}})
    assert nrt._attr_icon == TIME_ICON

    # Discovery config with icon overrides
    nrt.update_discovery_config({CONF_CONFIG: {CONF_ICON: "mdi:clock"}})
    assert nrt._attr_icon == "mdi:clock"


@pytest.mark.asyncio
async def test_async_set_value_sends_event_message(hass: HomeAssistant) -> None:
    """async_set_value should send an event_message with ISO time payload."""
    conn = FakeConnection()
    # Use an integer iden because Home Assistant's event_message expects an int iden
    config: dict[str, Any] = {
        CONF_ID: 2,
        CONF_SERVER_ID: "s1",
        CONF_NODE_ID: "n1",
        CONF_CONFIG: {},
    }
    nrt = NodeRedTime(hass, config, conn)

    await nrt.async_set_value(dt_time(5, 6, 7))

    expected = event_message(
        2,
        {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: dt_time(5, 6, 7).isoformat()},
    )
    # event_message returns a dict-like structure; compare sent message to expected
    assert conn.sent == expected


def test_class_attributes() -> None:
    """Class-level attributes should be set correctly."""
    assert NodeRedTime._bidirectional is True
    assert NodeRedTime.component == CONF_TIME
