"""Binary sensor platform for nodered."""
from numbers import Number

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    CONF_STATE,
    STATE_HOME,
    STATE_ON,
    STATE_OPEN,
    STATE_UNLOCKED,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import NodeRedEntity
from .const import CONF_BINARY_SENSOR, NODERED_DISCOVERY_NEW


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up sensor platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_devices)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_BINARY_SENSOR),
        async_discover,
    )


async def _async_setup_entity(hass, config, async_add_devices):
    """Set up the Node-RED binary-sensor."""
    async_add_devices([NodeRedBinarySensor(hass, config)])


class NodeRedBinarySensor(NodeRedEntity, BinarySensorEntity):
    """Node-RED binary-sensor class."""

    on_states = (
        "1",
        "true",
        "yes",
        "enable",
        STATE_ON,
        STATE_OPEN,
        STATE_HOME,
        STATE_UNLOCKED,
    )
    _component = CONF_BINARY_SENSOR

    def __init__(self, hass, config):
        """Initialize the binary sensor."""
        super().__init__(hass, config)
        self._attr_state = config.get(CONF_STATE)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        value = self._attr_state

        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.lower().strip()
            if value in NodeRedBinarySensor.on_states:
                return True
        elif isinstance(value, Number):
            return value != 0

        return False

    def update_entity_state_attributes(self, msg):
        """Update entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_state = msg.get(CONF_STATE)
