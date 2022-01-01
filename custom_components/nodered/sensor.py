"""Sensor platform for nodered."""
from datetime import datetime
import logging
from typing import Optional

from dateutil import parser
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_STATE, CONF_UNIT_OF_MEASUREMENT
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import NodeRedEntity
from .const import (
    CONF_CONFIG,
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
        self._attr_unit_of_measurement = None
        self._attr_native_value = config.get(CONF_STATE)
        self._attr_native_unit_of_measurement = self._config.get(
            CONF_UNIT_OF_MEASUREMENT
        )
        self._attr_state_class = self._config.get(CONF_STATE_CLASS)

    @property
    def last_reset(self) -> Optional[datetime]:
        """Return the last reset."""
        try:
            return parser.parse(self._config.get(CONF_LAST_RESET))
        except (ValueError, TypeError):
            return None

    def update_entity_state_attributes(self, msg):
        """Update entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_native_value = msg.get(CONF_STATE)

    def update_discovery_config(self, msg):
        """Update entity config."""
        super().update_discovery_config(msg)
        self._attr_native_unit_of_measurement = msg[CONF_CONFIG].get(
            CONF_UNIT_OF_MEASUREMENT
        )
        self._attr_unit_of_measurement = None
