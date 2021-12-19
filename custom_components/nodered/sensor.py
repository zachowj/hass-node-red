"""Sensor platform for nodered."""
from datetime import date, datetime
import logging
from typing import Optional, Union

from dateutil import parser
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_STATE, CONF_UNIT_OF_MEASUREMENT
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.typing import StateType

from . import NodeRedEntity
from .const import (
    CONF_ATTRIBUTES,
    CONF_LAST_RESET,
    CONF_SENSOR,
    CONF_STATE_CLASS,
    NODERED_DISCOVERY_NEW,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_SENSOR),
        async_discover,
    )


async def _async_setup_entity(hass, config, async_add_entities):
    """Set up the Node-RED sensor."""
    async_add_entities([NodeRedSensor(hass, config)])


class NodeRedSensor(NodeRedEntity, SensorEntity):
    """Node-RED Sensor class."""

    _component = CONF_SENSOR

    def __init__(self, hass, config):
        """Initialize the sensor."""
        super().__init__(hass, config)
        self._state = config.get(CONF_STATE)
        self.attr = config.get(CONF_ATTRIBUTES, {})

    @property
    def native_value(self) -> Union[StateType, date, datetime]:
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self) -> Union[str, None]:
        """Return the unit of measurement of this entity, if any."""
        return self._config.get(CONF_UNIT_OF_MEASUREMENT)

    @property
    def state_class(self) -> Optional[str]:
        """Return the state class."""
        return self._config.get(CONF_STATE_CLASS)

    @property
    def last_reset(self) -> Optional[datetime]:
        """Return the last reset."""
        try:
            return parser.parse(self._config.get(CONF_LAST_RESET))
        except (ValueError, TypeError):
            return None
