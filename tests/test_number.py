import pytest

from custom_components.nodered.const import CONF_CONFIG, CONF_NUMBER
import custom_components.nodered.number as number
from custom_components.nodered.number import NodeRedNumber


class FakeConnection:
    def __init__(self):
        self.sent = None

    def send_message(self, msg):
        self.sent = msg


def test_update_config_sets_number_specific_attributes(monkeypatch):
    """update_config should set number-specific attributes from config update message."""
    def mock_init(self, hass, config):
        self._config = {}
    
    monkeypatch.setattr(
        number.NodeRedEntity, "__init__", mock_init
    )
    # Ensure parent update_config does not run
    monkeypatch.setattr(
        number.NodeRedEntity, "update_config", lambda self, msg: None
    )

    connection = FakeConnection()
    config = {number.CONF_ID: "id-1"}
    node = NodeRedNumber(None, config, connection)

    # Set initial values to verify they change
    node._attr_native_min_value = 0
    node._attr_native_max_value = 100
    node._attr_native_step = 1
    node._attr_mode = number.NumberMode.AUTO
    node._attr_native_unit_of_measurement = None

    # Config update message
    msg = {
        CONF_CONFIG: {
            number.CONF_MIN_VALUE: 10,
            number.CONF_MAX_VALUE: 200,
            number.CONF_STEP_VALUE: 5,
            number.CONF_MODE: number.NumberMode.SLIDER,
            number.CONF_UNIT_OF_MEASUREMENT: "°C",
        }
    }

    node.update_config(msg)

    assert getattr(node, "_attr_native_min_value") == 10
    assert getattr(node, "_attr_native_max_value") == 200
    assert getattr(node, "_attr_native_step") == 5
    assert getattr(node, "_attr_mode") == number.NumberMode.SLIDER
    assert getattr(node, "_attr_native_unit_of_measurement") == "°C"


def test_update_config_handles_partial_config(monkeypatch):
    """update_config should handle partial config updates gracefully."""
    def mock_init(self, hass, config):
        self._config = {}
    
    monkeypatch.setattr(
        number.NodeRedEntity, "__init__", mock_init
    )
    # Ensure parent update_config does not run
    monkeypatch.setattr(
        number.NodeRedEntity, "update_config", lambda self, msg: None
    )

    connection = FakeConnection()
    config = {number.CONF_ID: "id-2"}
    node = NodeRedNumber(None, config, connection)

    # Set initial values to verify only specified attributes change
    node._attr_native_min_value = 0
    node._attr_native_max_value = 100
    node._attr_native_step = 1
    node._attr_mode = number.NumberMode.AUTO
    node._attr_native_unit_of_measurement = None

    # Partial config update message (only step_value)
    msg = {
        CONF_CONFIG: {
            number.CONF_STEP_VALUE: 10,
        }
    }

    node.update_config(msg)

    # Only step should change
    assert getattr(node, "_attr_native_min_value") == 0
    assert getattr(node, "_attr_native_max_value") == 100
    assert getattr(node, "_attr_native_step") == 10
    assert getattr(node, "_attr_mode") == number.NumberMode.AUTO
    assert getattr(node, "_attr_native_unit_of_measurement") is None


def test_update_config_handles_empty_config(monkeypatch):
    """update_config should handle empty config gracefully."""
    def mock_init(self, hass, config):
        self._config = {}
    
    monkeypatch.setattr(
        number.NodeRedEntity, "__init__", mock_init
    )
    # Ensure parent update_config does not run
    monkeypatch.setattr(
        number.NodeRedEntity, "update_config", lambda self, msg: None
    )

    connection = FakeConnection()
    config = {number.CONF_ID: "id-3"}
    node = NodeRedNumber(None, config, connection)

    # Set initial values to verify they don't change
    node._attr_native_min_value = 5
    node._attr_native_max_value = 50
    node._attr_native_step = 2
    node._attr_mode = number.NumberMode.BOX
    node._attr_native_unit_of_measurement = "km"

    # Empty config
    msg = {CONF_CONFIG: {}}

    node.update_config(msg)

    # Values should remain unchanged
    assert getattr(node, "_attr_native_min_value") == 5
    assert getattr(node, "_attr_native_max_value") == 50
    assert getattr(node, "_attr_native_step") == 2
    assert getattr(node, "_attr_mode") == number.NumberMode.BOX
    assert getattr(node, "_attr_native_unit_of_measurement") == "km"


def test_update_discovery_config_sets_number_attributes(monkeypatch):
    """update_discovery_config should set number-specific attributes from discovery config."""
    def mock_init(self, hass, config):
        self._config = {}
    
    monkeypatch.setattr(
        number.NodeRedEntity, "__init__", mock_init
    )
    # Ensure parent update_discovery_config does not run
    monkeypatch.setattr(
        number.NodeRedEntity, "update_discovery_config", lambda self, msg: None
    )

    connection = FakeConnection()
    config = {number.CONF_ID: "id-4"}
    node = NodeRedNumber(None, config, connection)

    discovery = {
        CONF_CONFIG: {
            number.CONF_ICON: "mdi:test-icon",
            number.CONF_MIN_VALUE: 20,
            number.CONF_MAX_VALUE: 300,
            number.CONF_STEP_VALUE: 15,
            number.CONF_MODE: number.NumberMode.SLIDER,
            number.CONF_UNIT_OF_MEASUREMENT: "mph",
        }
    }

    # Set _config to match the discovery config
    node._config = discovery[CONF_CONFIG]
    node.update_discovery_config(discovery)

    assert getattr(node, "_attr_icon") == "mdi:test-icon"
    assert getattr(node, "_attr_native_min_value") == 20
    assert getattr(node, "_attr_native_max_value") == 300
    assert getattr(node, "_attr_native_step") == 15
    assert getattr(node, "_attr_mode") == number.NumberMode.SLIDER
    assert getattr(node, "_attr_native_unit_of_measurement") == "mph"


def test_class_attributes():
    """Test that the class has correct constant attributes."""
    # These are defined directly on the class
    assert NodeRedNumber._bidirectional is True
    assert NodeRedNumber._component == CONF_NUMBER
