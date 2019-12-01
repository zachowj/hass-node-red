"""Sensor platform for nodered."""
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import CONF_STATE

from . import NodeRedEntity
from .const import (
    CONF_ATTRIBUTES,
    CONF_SENSOR,
    NODERED_DISCOVERY_NEW,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensor platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities)

    async_dispatcher_connect(
        hass, NODERED_DISCOVERY_NEW.format(CONF_SENSOR), async_discover,
    )


async def _async_setup_entity(hass, config, async_add_entities):
    """Set up the Node-RED sensor."""
    async_add_entities([NodeRedSensor(hass, config)])


class NodeRedSensor(NodeRedEntity):
    """Node-RED Sensor class."""

    def __init__(self, hass, config):
        super().__init__(hass, config)
        self._component = CONF_SENSOR
        self._state = config.get(CONF_STATE)
        self.attr = config.get(CONF_ATTRIBUTES, {})

