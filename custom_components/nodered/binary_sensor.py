"""Binary sensor platform for nodered."""
from numbers import Number

from homeassistant.const import (
    CONF_STATE,
    STATE_HOME,
    STATE_LOCKED,
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import NodeRedEntity
from .const import CONF_ATTRIBUTES, CONF_BINARY_SENSOR, NODERED_DISCOVERY_NEW


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up sensor platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_devices)

    async_dispatcher_connect(
        hass, NODERED_DISCOVERY_NEW.format(CONF_BINARY_SENSOR), async_discover,
    )


async def _async_setup_entity(hass, config, async_add_devices):
    """Set up the Node-RED binary-sensor."""
    async_add_devices([NodeRedBinarySensor(hass, config)])


class NodeRedBinarySensor(NodeRedEntity):
    """Node-RED binary-sensor class."""

    on_states = (
        "1",
        "true",
        "yes",
        "enable",
        STATE_ON,
        STATE_OPEN,
        STATE_HOME,
        STATE_LOCKED,
    )

    def __init__(self, hass, config):
        """Initialize the binary sensor."""
        super().__init__(hass, config)
        self._component = CONF_BINARY_SENSOR
        self._state = config.get(CONF_STATE)
        self.attr = config.get(CONF_ATTRIBUTES, {})

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        value = self._state

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.lower().strip()
            if value in NodeRedBinarySensor.on_states:
                return True
        elif isinstance(value, Number):
            return value != 0

        return False

    @property
    def state(self):
        """Return the state of the binary sensor."""
        return STATE_ON if self.is_on else STATE_OFF
