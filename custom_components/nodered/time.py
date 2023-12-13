"""Sensor platform for nodered."""
import logging

from dateutil import parser
from homeassistant.components.time import TimeEntity
from homeassistant.components.websocket_api import event_message
from homeassistant.const import CONF_ICON, CONF_ID, CONF_TYPE
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import NodeRedEntity
from .const import (
    CONF_CONFIG,
    CONF_TIME,
    EVENT_VALUE_CHANGE,
    NODERED_DISCOVERY_NEW,
    TIME_ICON,
)

_LOGGER = logging.getLogger(__name__)


CONF_STATE = "state"
CONF_VALUE = "value"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the time platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities, connection)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_TIME),
        async_discover,
    )


async def _async_setup_entity(hass, config, async_add_entities, connection):
    """Set up the Node-RED time."""

    async_add_entities([NodeRedTime(hass, config, connection)])


def _convert_string_to_time(value):
    """Convert string to time."""
    if value is None:
        return None
    try:
        return parser.parse(value).time()
    except ValueError:
        _LOGGER.error(f"Unable to parse time: {value}")
        return None


class NodeRedTime(NodeRedEntity, TimeEntity):
    """Node-RED time class."""

    _attr_native_value = None
    _bidirectional = True
    _component = CONF_TIME

    def __init__(self, hass, config, connection):
        """Initialize the time."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

    async def async_set_value(self, value) -> None:
        """Set new value."""
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: value}
            )
        )

    def update_entity_state_attributes(self, msg):
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_native_value = _convert_string_to_time(msg.get(CONF_STATE))

    def update_discovery_config(self, msg):
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = msg[CONF_CONFIG].get(CONF_ICON, TIME_ICON)
