"""Select platform for nodered."""

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON, CONF_STATE, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CONFIG,
    CONF_OPTIONS,
    CONF_SELECT,
    CONF_VALUE,
    EVENT_VALUE_CHANGE,
    SELECT_ICON,
)
from .entity import NodeRedEntity, async_setup_discovery


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the text platform."""

    async_setup_discovery(hass, config_entry, NodeRedSelect, async_add_entities)


class NodeRedSelect(NodeRedEntity, SelectEntity):
    """Node-RED text class."""

    _bidirectional = True
    component = CONF_SELECT

    async def async_select_option(self, option: str) -> None:
        """Set new option."""
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: option}
            )
        )

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_current_option = msg.get(CONF_STATE)

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = msg[CONF_CONFIG].get(CONF_ICON, SELECT_ICON)
        if msg[CONF_CONFIG].get(CONF_OPTIONS) is not None:
            self._attr_options = msg[CONF_CONFIG].get(CONF_OPTIONS)
