"""Sensor platform for nodered."""

from datetime import time
from typing import Any

from dateutil import parser
import voluptuous as vol

from homeassistant.components.time import TimeEntity
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON, CONF_STATE, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CONFIG, CONF_TIME, CONF_VALUE, EVENT_VALUE_CHANGE, TIME_ICON
from .entity import NodeRedEntity, async_setup_discovery


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the time platform."""

    async_setup_discovery(hass, config_entry, NodeRedTime, async_add_entities)


def _convert_string_to_time(value: str | None) -> None | time:
    """Convert string to time."""
    if value is None:
        return None
    try:
        return parser.parse(value).time()
    except (ValueError, TypeError, OverflowError) as err:
        raise vol.Invalid(f"'{value}' is not a valid time", path=[CONF_STATE]) from err


class NodeRedTime(NodeRedEntity, TimeEntity):
    """Node-RED time class."""

    _attr_native_value = None
    _bidirectional = True
    component = CONF_TIME
    update_attrs = (
        *NodeRedEntity.update_attrs,
        "_attr_native_value",
    )

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
