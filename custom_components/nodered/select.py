"""Select platform for nodered."""
from homeassistant.components.select import SelectEntity
from homeassistant.components.websocket_api import event_message
from homeassistant.const import CONF_ICON, CONF_ID, CONF_TYPE
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.nodered.number import CONF_VALUE

from . import NodeRedEntity
from .const import (
    CONF_CONFIG,
    CONF_OPTIONS,
    CONF_SELECT,
    EVENT_VALUE_CHANGE,
    NODERED_DISCOVERY_NEW,
    SELECT_ICON,
)

CONF_STATE = "state"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the text platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities, connection)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_SELECT),
        async_discover,
    )


async def _async_setup_entity(hass, config, async_add_entities, connection):
    """Set up the Node-RED text."""

    async_add_entities([NodeRedSelect(hass, config, connection)])


class NodeRedSelect(NodeRedEntity, SelectEntity):
    """Node-RED text class."""

    _bidirectional = True
    _component = CONF_SELECT

    def __init__(self, hass, config, connection):
        """Initialize the number."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

    async def async_select_option(self, option: str) -> None:
        """Set new option."""
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: option}
            )
        )

    def update_entity_state_attributes(self, msg):
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_current_option = msg.get(CONF_STATE)

    def update_discovery_config(self, msg):
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = msg[CONF_CONFIG].get(CONF_ICON, SELECT_ICON)
        if msg[CONF_CONFIG].get(CONF_OPTIONS) is not None:
            self._attr_options = msg[CONF_CONFIG].get(CONF_OPTIONS)
