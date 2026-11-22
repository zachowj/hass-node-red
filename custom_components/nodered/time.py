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
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import CONF_CONFIG, CONF_TIME, CONF_VALUE, EVENT_VALUE_CHANGE, TIME_ICON
from .entity import NodeRedEntity, async_setup_discovery, reject_null_state


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the time platform."""

    async_setup_discovery(hass, config_entry, NodeRedTime, async_add_entities)


def _convert_string_to_time(value: str) -> time:
    """Convert string to time."""
    try:
        return parser.parse(value).time()
    except (ValueError, TypeError, OverflowError) as err:
        raise vol.Invalid(f"'{value}' is not a valid time", path=[CONF_STATE]) from err


class NodeRedTime(NodeRedEntity, TimeEntity, RestoreEntity):
    """Node-RED time class."""

    _attr_native_value = None
    _bidirectional = True
    component = CONF_TIME
    update_attrs = (
        *NodeRedEntity.update_attrs,
        "_attr_native_value",
    )

    async def async_added_to_hass(self) -> None:
        """Restore the value if discovery didn't send one, else use midnight."""
        await super().async_added_to_hass()
        if self._attr_native_value is None and (
            last_state := await self.async_get_last_state()
        ):
            self._attr_native_value = dt_util.parse_time(last_state.state)
        if self._attr_native_value is None:
            self._attr_native_value = time(0, 0)

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
        reject_null_state(msg)
        super().update_entity_state_attributes(msg)
        if CONF_STATE in msg:
            self._attr_native_value = _convert_string_to_time(msg[CONF_STATE])

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = msg[CONF_CONFIG].get(CONF_ICON, TIME_ICON)
