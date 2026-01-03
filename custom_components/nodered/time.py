"""Sensor platform for nodered."""

from datetime import time
import logging
from typing import Any

from dateutil import parser

from homeassistant.components.time import TimeEntity
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON, CONF_ID, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CONFIG,
    CONF_TIME,
    EVENT_VALUE_CHANGE,
    NODERED_DISCOVERY_NEW,
    TIME_ICON,
)
from .entity import NodeRedEntity

_LOGGER = logging.getLogger(__name__)


CONF_STATE = "state"
CONF_VALUE = "value"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the time platform."""

    async def async_discover(
        config: dict[str, Any], connection: ActiveConnection
    ) -> None:
        await _async_setup_entity(hass, config, async_add_entities, connection)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            NODERED_DISCOVERY_NEW.format(CONF_TIME),
            async_discover,
        )
    )


async def _async_setup_entity(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    connection: ActiveConnection,
) -> None:
    """Set up the Node-RED time."""
    async_add_entities([NodeRedTime(hass, config, connection)])


def _convert_string_to_time(value: str | None) -> None | time:
    """Convert string to time."""
    if value is None:
        return None
    try:
        return parser.parse(value).time()
    except ValueError:
        _LOGGER.exception("Unable to parse time: %s", value)
        return None


class NodeRedTime(NodeRedEntity, TimeEntity):
    """Node-RED time class."""

    _attr_native_value = None
    _bidirectional = True
    component = CONF_TIME

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        connection: ActiveConnection,
    ) -> None:
        """Initialize the time."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

    async def async_set_value(self, value: time) -> None:
        """Set new value."""
        # Convert the datetime.time to an ISO-formatted string before sending.
        self._connection.send_message(
            event_message(
                self._message_id,
                {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: value.isoformat()},
            )
        )

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_native_value = _convert_string_to_time(msg.get(CONF_STATE))

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = msg[CONF_CONFIG].get(CONF_ICON, TIME_ICON)
