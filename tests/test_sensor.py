"""Tests for Node-RED sensor last_reset handling."""

from datetime import UTC, date, datetime
from typing import Any, cast

import pytest

from custom_components.nodered.const import (
    CONF_CONFIG,
    CONF_LAST_RESET,
    CONF_STATE_CLASS,
)
from custom_components.nodered.sensor import NodeRedSensor
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant


def test_update_discovery_config_sets_last_reset_for_timestamp(
    hass: HomeAssistant,
) -> None:
    """Cache valid last_reset ISO string as a datetime for timestamp devices."""
    config = {"id": "id-1", "server_id": "s1", "node_id": "node-1", CONF_CONFIG: {}}
    node = NodeRedSensor(hass, config)

    last_reset_str = "2020-01-01T12:34:56Z"
    discovery = {
        CONF_CONFIG: {
            CONF_LAST_RESET: last_reset_str,
            CONF_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP,
        }
    }

    # Apply discovery update
    node.update_discovery_config(discovery)

    # Cached value should be present and be a datetime matching parsed value
    assert "last_reset" in node.__dict__
    assert isinstance(node.last_reset, datetime)
    assert node.last_reset == datetime.fromisoformat("2020-01-01T12:34:56+00:00")


def test_update_discovery_config_sets_last_reset_for_date_device(
    hass: HomeAssistant,
) -> None:
    """Valid last_reset ISO string should be cached as date for date device class."""
    config = {"id": "id-2", "server_id": "s1", "node_id": "node-2", CONF_CONFIG: {}}
    node = NodeRedSensor(hass, config)

    last_reset_str = "2020-01-01T00:00:00Z"
    discovery = {
        CONF_CONFIG: {
            CONF_LAST_RESET: last_reset_str,
            CONF_DEVICE_CLASS: SensorDeviceClass.DATE,
        }
    }

    node.update_discovery_config(discovery)

    assert "last_reset" in node.__dict__
    assert isinstance(node.last_reset, date)
    assert node.last_reset == date(2020, 1, 1)


def test_update_discovery_config_invalid_last_reset_removes_cached(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid last_reset should log and remove any cached value."""
    config = {"id": "id-3", "server_id": "s1", "node_id": "node-3", CONF_CONFIG: {}}
    node = NodeRedSensor(hass, config)

    # Seed a cached value
    node.__dict__["last_reset"] = datetime(2019, 1, 1, tzinfo=UTC)

    discovery = {
        CONF_CONFIG: {
            CONF_LAST_RESET: "not-a-date",
            CONF_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP,
        }
    }

    caplog.clear()
    node.update_discovery_config(discovery)

    # Cached value should be removed
    assert "last_reset" not in node.__dict__

    # There should be an exception-level log indicating invalid date
    found = any(
        "requires last_reset to be an iso date formatted string" in rec.getMessage()
        for rec in caplog.records
    )
    assert found


def test_update_discovery_config_ignores_last_reset_without_valid_class(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """If discovery provides last_reset but sensor lacks a timestamp/date.

    Device class or an allowed state_class, it should be ignored and a
    warning should be logged.
    """
    config = {"id": "id-10", "server_id": "s1", "node_id": "node-10", CONF_CONFIG: {}}
    node = NodeRedSensor(hass, config)

    last_reset_str = "2020-01-01T12:34:56Z"
    discovery = {CONF_CONFIG: {CONF_LAST_RESET: last_reset_str}}

    caplog.clear()
    node.update_discovery_config(discovery)

    # Should not cache last_reset when neither device_class nor supported
    # state_class is present
    assert "last_reset" not in node.__dict__
    assert any("ignoring last_reset" in rec.getMessage() for rec in caplog.records)


def test_convert_state_invalid_timestamp_returns_none_and_logs(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid timestamp/date state should return None and log an exception."""
    node = NodeRedSensor(
        hass, {"id": "id-4", "server_id": "s1", "node_id": "node-4", CONF_CONFIG: {}}
    )

    # Test TIMESTAMP device class with invalid string
    node._attr_device_class = SensorDeviceClass.TIMESTAMP
    caplog.clear()
    res = node.convert_state("not-a-date")
    assert res is None
    assert any(
        "has a timestamp device class" in rec.getMessage() for rec in caplog.records
    )

    # Test TIMESTAMP device class with None state should not log an exception
    caplog.clear()
    res_none = node.convert_state(None)
    assert res_none is None
    assert not any(
        "has a timestamp device class" in rec.getMessage() for rec in caplog.records
    )


def test_convert_state_invalid_date_returns_none_and_logs(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid date state should return None and log an exception."""
    node = NodeRedSensor(
        hass, {"id": "id-5", "server_id": "s1", "node_id": "node-5", CONF_CONFIG: {}}
    )

    # Test DATE device class
    node._attr_device_class = SensorDeviceClass.DATE
    caplog.clear()
    res = node.convert_state("not-a-date")
    assert res is None
    assert any(
        "has a timestamp device class" in rec.getMessage() for rec in caplog.records
    )


def test_convert_state_valid_timestamp_and_date(hass: HomeAssistant) -> None:
    """Valid timestamp/date strings should be parsed to datetime/date respectively."""
    node = NodeRedSensor(
        hass, {"id": "id-6", "server_id": "s1", "node_id": "node-6", CONF_CONFIG: {}}
    )

    node._attr_device_class = SensorDeviceClass.TIMESTAMP
    ts = node.convert_state("2021-02-03T04:05:06Z")
    assert isinstance(ts, datetime)
    assert ts == datetime.fromisoformat("2021-02-03T04:05:06+00:00")

    # Numeric timestamp in seconds

    now = datetime.fromtimestamp(1612314906, tz=UTC)
    sec_ts = int(now.timestamp())
    ts2 = node.convert_state(sec_ts)
    assert isinstance(ts2, datetime)
    assert ts2 == now

    # Numeric timestamp in milliseconds and as string
    ms_ts = int(now.timestamp() * 1000)
    ts3 = node.convert_state(ms_ts)
    assert isinstance(ts3, datetime)
    assert ts3 == now

    ts4 = node.convert_state(str(ms_ts))
    assert isinstance(ts4, datetime)
    assert ts4 == now

    node._attr_device_class = SensorDeviceClass.DATE
    d = node.convert_state("2021-02-03T00:00:00Z")
    assert isinstance(d, date)
    assert d == date(2021, 2, 3)


def test_validate_and_cache_last_reset_direct(hass: HomeAssistant) -> None:
    """Directly calling the private validator should parse/cache and invalidate."""
    node = NodeRedSensor(
        hass, {"id": "id-7", "server_id": "s1", "node_id": "node-7", CONF_CONFIG: {}}
    )

    # Valid timestamp
    node._attr_device_class = SensorDeviceClass.TIMESTAMP
    node._validate_and_cache_last_reset("2020-01-01T12:34:56Z")
    assert "last_reset" in node.__dict__
    assert isinstance(node.last_reset, datetime)

    # Valid date
    node._attr_device_class = SensorDeviceClass.DATE
    node._validate_and_cache_last_reset("2020-01-02T00:00:00Z")
    assert isinstance(node.last_reset, date)

    # Invalid should remove cached and log
    node.__dict__["last_reset"] = datetime(2018, 1, 1, tzinfo=UTC)
    node._attr_device_class = SensorDeviceClass.TIMESTAMP
    node._validate_and_cache_last_reset("not-a-date")
    assert "last_reset" not in node.__dict__


def test_convert_state_handles_extreme_and_negative_numbers(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Extreme numeric timestamps should fail; negative timestamps should parse."""
    node = NodeRedSensor(
        hass, {"id": "id-8", "server_id": "s1", "node_id": "node-8", CONF_CONFIG: {}}
    )

    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    # Extremely large number (likely overflow) should return None and log
    big_ts = 10**20
    caplog.clear()
    res_big = node.convert_state(big_ts)
    assert res_big is None
    assert any("Invalid timestamp" in rec.getMessage() for rec in caplog.records)

    # Negative timestamp (before epoch) should parse to a datetime
    caplog.clear()
    neg_ts = -1000000000  # about 1938-04-24
    res_neg = node.convert_state(neg_ts)
    assert isinstance(res_neg, datetime)


def test_update_entity_state_attributes_does_not_overwrite_when_state_missing(
    hass: HomeAssistant,
) -> None:
    """If a message lacks a state key, the native value should not be overwritten."""
    node = NodeRedSensor(
        hass, {"id": "id-9", "server_id": "s1", "node_id": "node-9", CONF_CONFIG: {}}
    )
    node._attr_native_value = "initial"

    # Message with only attributes should not change native value
    node.update_entity_state_attributes({"attributes": {"a": 1}})
    assert node._attr_native_value == "initial"


def _make_node(hass: HomeAssistant, node_id: str) -> NodeRedSensor:
    return NodeRedSensor(
        hass, {"id": node_id, "server_id": "s1", "node_id": node_id, "config": {}}
    )


def test_convert_state_accepts_int_float_and_numeric_strings(
    hass: HomeAssistant,
) -> None:
    """Integer, float and numeric-string timestamps should parse to datetime."""
    node = _make_node(hass, "id-int-float")
    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    # seconds as int
    sec = 1612314906
    res_sec = node.convert_state(sec)
    assert isinstance(res_sec, datetime)
    assert res_sec == datetime.fromtimestamp(sec, tz=UTC)

    # seconds as float
    sec_f = 1612314906.123
    res_sec_f = node.convert_state(sec_f)
    assert isinstance(res_sec_f, datetime)
    assert res_sec_f == datetime.fromtimestamp(sec_f, tz=UTC)

    # numeric string (float)
    res_str = node.convert_state(str(sec_f))
    assert isinstance(res_str, datetime)
    assert res_str == datetime.fromtimestamp(float(str(sec_f)), tz=UTC)

    # milliseconds as int heuristic
    now = datetime.fromtimestamp(1612314906, tz=UTC)
    ms = int(now.timestamp() * 1000)
    res_ms = node.convert_state(ms)
    assert isinstance(res_ms, datetime)
    assert res_ms == datetime.fromtimestamp(ms / 1000.0, tz=UTC)


def test_convert_state_preserves_fractional_seconds_for_decimal_strings(
    hass: HomeAssistant,
) -> None:
    """Decimal numeric strings should preserve fractional seconds."""
    node = _make_node(hass, "id-decimal")
    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    s = "1612314906.789"
    expected = datetime.fromtimestamp(float(s), tz=UTC)
    res = node.convert_state(s)
    assert isinstance(res, datetime)
    assert res == expected


def test_convert_state_zero_and_negative_timestamps(hass: HomeAssistant) -> None:
    """Zero and negative timestamps should parse correctly."""
    node = _make_node(hass, "id-zero-neg")
    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    res_zero = node.convert_state(0)
    assert isinstance(res_zero, datetime)
    assert res_zero == datetime.fromtimestamp(0, tz=UTC)

    res_neg = node.convert_state(-1000000000)  # before epoch
    assert isinstance(res_neg, datetime)
    assert res_neg == datetime.fromtimestamp(-1000000000, tz=UTC)


def test_convert_state_large_overflow_logs_and_returns_none(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Extremely large numeric timestamps should return None and log an error."""
    node = _make_node(hass, "id-big")
    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    big = 10**20
    caplog.clear()
    res = node.convert_state(big)
    assert res is None
    assert any("Invalid timestamp" in rec.getMessage() for rec in caplog.records)


def test_update_discovery_config_accepts_last_reset_with_total_state_class(
    hass: HomeAssistant,
) -> None:
    """last_reset should be accepted when state_class is 'total'."""
    config = {"id": "id-11", "server_id": "s1", "node_id": "node-11", CONF_CONFIG: {}}
    node = NodeRedSensor(hass, config)

    last_reset_str = "2021-03-04T05:06:07Z"
    discovery = {
        CONF_CONFIG: {CONF_LAST_RESET: last_reset_str, CONF_STATE_CLASS: "total"}
    }

    node.update_discovery_config(discovery)

    assert "last_reset" in node.__dict__
    assert isinstance(node.last_reset, datetime)
    assert node.last_reset == datetime.fromisoformat("2021-03-04T05:06:07+00:00")


def test_update_discovery_config_updates_unit_and_state_class(
    hass: HomeAssistant,
) -> None:
    """Unit of measurement and state_class from discovery should be applied."""
    config = {"id": "id-12", "server_id": "s1", "node_id": "node-12", CONF_CONFIG: {}}
    node = NodeRedSensor(hass, config)

    discovery = {
        CONF_CONFIG: {CONF_UNIT_OF_MEASUREMENT: "°C", CONF_STATE_CLASS: "measurement"}
    }

    node.update_discovery_config(discovery)

    assert node._attr_native_unit_of_measurement == "°C"
    assert node._attr_unit_of_measurement is None
    assert node._attr_state_class == "measurement"


def test_entity_category_mapper_logs_for_config_and_returns_diagnostic(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """entity_category_mapper should warn for 'config' and return DIAGNOSTIC for 'diagnostic'."""
    node = NodeRedSensor(
        hass, {"id": "id-13", "server_id": "s1", "node_id": "node-13", CONF_CONFIG: {}}
    )

    # 'config' should warn and return None

    caplog.clear()
    node.entity_category_mapper("config")
    assert any(
        "has category 'config' which is not supported" in rec.getMessage()
        for rec in caplog.records
    )

    # 'diagnostic' should return the enum
    assert node.entity_category_mapper("diagnostic") is EntityCategory.DIAGNOSTIC


def test_convert_state_non_string_non_numeric_logs_and_returns_none(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Non-string, non-numeric state for timestamp device should log and return None."""
    node = NodeRedSensor(
        hass, {"id": "id-14", "server_id": "s1", "node_id": "node-14", CONF_CONFIG: {}}
    )
    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    caplog.clear()
    res = node.convert_state(cast(Any, [1, 2, 3]))
    assert res is None
    assert any(
        "has a timestamp device class" in rec.getMessage() for rec in caplog.records
    )


def test_update_entity_state_attributes_updates_native_when_state_present(
    hass: HomeAssistant,
) -> None:
    """When a state key is present, native value should be updated (and converted)."""
    node = NodeRedSensor(
        hass, {"id": "id-15", "server_id": "s1", "node_id": "node-15", CONF_CONFIG: {}}
    )
    node._attr_device_class = SensorDeviceClass.TIMESTAMP

    msg = {"state": "2022-04-05T06:07:08Z", "attributes": {"foo": "bar"}}
    node.update_entity_state_attributes(msg)

    assert isinstance(node._attr_native_value, datetime)
    assert node._attr_native_value == datetime.fromisoformat(
        "2022-04-05T06:07:08+00:00"
    )


def test_update_discovery_config_overwrites_existing_last_reset(
    hass: HomeAssistant,
) -> None:
    """Providing a new valid last_reset should overwrite any existing cached value."""
    config = {
        "id": "id-16",
        "server_id": "s1",
        "node_id": "node-16",
        CONF_CONFIG: {CONF_STATE_CLASS: "total"},
    }
    node = NodeRedSensor(hass, config)

    # Seed an existing last_reset
    node.__dict__["last_reset"] = datetime(2000, 1, 1, tzinfo=UTC)

    new_last = "2023-01-02T03:04:05Z"
    discovery = {
        CONF_CONFIG: {
            CONF_STATE_CLASS: "total",
            CONF_LAST_RESET: new_last,
        }
    }  # no device class; default behavior: ignored unless state_class/device_class set

    # Set device class so last_reset will be validated and cached
    node._attr_device_class = SensorDeviceClass.TIMESTAMP
    node.update_discovery_config(discovery)

    assert "last_reset" in node.__dict__
    assert node.last_reset == datetime.fromisoformat("2023-01-02T03:04:05+00:00")
