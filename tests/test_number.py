"""Tests for Node-RED number entity."""

from custom_components.nodered import number
from custom_components.nodered.const import CONF_CONFIG, CONF_NUMBER
from custom_components.nodered.number import NodeRedNumber
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection

# Constants for test values
MIN_VALUE = 10
MAX_VALUE = 200
STEP_VALUE = 5
PARTIAL_STEP_VALUE = 10
EMPTY_MIN_VALUE = 5
EMPTY_MAX_VALUE = 50
EMPTY_STEP_VALUE = 2
DISCOVERY_MIN_VALUE = 20
DISCOVERY_MAX_VALUE = 300
DISCOVERY_STEP_VALUE = 15


def test_update_config_sets_number_specific_attributes(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_config sets number-specific attributes from a config message."""
    connection = fake_connection
    config = {
        number.CONF_ID: "id-1",
        "server_id": "s1",
        "node_id": "n1",
        CONF_CONFIG: {},
    }
    node = NodeRedNumber(hass, config, connection)

    # Set initial values to verify they change
    node._attr_native_min_value = 0
    node._attr_native_max_value = 100
    node._attr_native_step = 1
    node._attr_mode = number.NumberMode.AUTO
    node._attr_native_unit_of_measurement = None

    # Config update message
    msg = {
        CONF_CONFIG: {
            number.CONF_MIN_VALUE: MIN_VALUE,
            number.CONF_MAX_VALUE: MAX_VALUE,
            number.CONF_STEP_VALUE: STEP_VALUE,
            number.CONF_MODE: number.NumberMode.SLIDER,
            number.CONF_UNIT_OF_MEASUREMENT: "°C",
        }
    }

    node.update_config(msg)

    assert node._attr_native_min_value == MIN_VALUE
    assert node._attr_native_max_value == MAX_VALUE
    assert node._attr_native_step == STEP_VALUE
    assert node._attr_mode == number.NumberMode.SLIDER
    assert node._attr_native_unit_of_measurement == "°C"


def test_update_config_handles_partial_config(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_config should handle partial config updates gracefully."""
    connection = fake_connection
    config = {
        number.CONF_ID: "id-2",
        "server_id": "s1",
        "node_id": "n2",
        CONF_CONFIG: {},
    }
    node = NodeRedNumber(hass, config, connection)

    # Set initial values to verify only specified attributes change
    init_min_value = 0
    init_max_value = 100
    node._attr_native_min_value = init_min_value
    node._attr_native_max_value = init_max_value
    node._attr_native_step = 1
    node._attr_mode = number.NumberMode.AUTO
    node._attr_native_unit_of_measurement = None

    # Partial config update message (only step_value)
    msg = {
        CONF_CONFIG: {
            number.CONF_STEP_VALUE: PARTIAL_STEP_VALUE,
        }
    }

    node.update_config(msg)

    # Only step should change
    assert node._attr_native_min_value == init_min_value
    assert node._attr_native_max_value == init_max_value
    assert node._attr_native_step == PARTIAL_STEP_VALUE
    assert node._attr_mode == number.NumberMode.AUTO
    assert node._attr_native_unit_of_measurement is None


def test_update_config_handles_empty_config(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_config should handle empty config gracefully."""
    connection = fake_connection
    config = {
        number.CONF_ID: "id-3",
        "server_id": "s1",
        "node_id": "n3",
        CONF_CONFIG: {},
    }
    node = NodeRedNumber(hass, config, connection)

    # Set initial values to verify they don't change
    node._attr_native_min_value = EMPTY_MIN_VALUE
    node._attr_native_max_value = EMPTY_MAX_VALUE
    node._attr_native_step = EMPTY_STEP_VALUE
    node._attr_mode = number.NumberMode.BOX
    node._attr_native_unit_of_measurement = "km"

    # Empty config
    msg = {CONF_CONFIG: {}}

    node.update_config(msg)

    # Values should remain unchanged
    assert node._attr_native_min_value == EMPTY_MIN_VALUE
    assert node._attr_native_max_value == EMPTY_MAX_VALUE
    assert node._attr_native_step == EMPTY_STEP_VALUE
    assert node._attr_mode == number.NumberMode.BOX
    assert node._attr_native_unit_of_measurement == "km"


def test_update_discovery_config_sets_number_attributes(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """update_discovery_config sets number-specific attributes from discovery config."""
    connection = fake_connection
    config = {
        number.CONF_ID: "id-4",
        "server_id": "s4",
        "node_id": "n4",
        CONF_CONFIG: {},
    }
    node = NodeRedNumber(hass, config, connection)

    discovery = {
        CONF_CONFIG: {
            number.CONF_ICON: "mdi:test-icon",
            number.CONF_MIN_VALUE: DISCOVERY_MIN_VALUE,
            number.CONF_MAX_VALUE: DISCOVERY_MAX_VALUE,
            number.CONF_STEP_VALUE: DISCOVERY_STEP_VALUE,
            number.CONF_MODE: number.NumberMode.SLIDER,
            number.CONF_UNIT_OF_MEASUREMENT: "mph",
        }
    }

    # Set _config to match the discovery config
    node._config = discovery[CONF_CONFIG]
    node.update_discovery_config(discovery)

    assert node._attr_icon == "mdi:test-icon"
    assert node._attr_native_min_value == DISCOVERY_MIN_VALUE
    assert node._attr_native_max_value == DISCOVERY_MAX_VALUE
    assert node._attr_native_step == DISCOVERY_STEP_VALUE
    assert node._attr_mode == number.NumberMode.SLIDER
    assert node._attr_native_unit_of_measurement == "mph"


def test_class_attributes() -> None:
    """Test that the class has correct constant attributes."""
    # These are defined directly on the class
    assert NodeRedNumber._bidirectional is True
    assert NodeRedNumber.component == CONF_NUMBER
