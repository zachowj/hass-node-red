"""Sensor platform for nodered."""
from homeassistant.components.text import RestoreText, TextMode
from homeassistant.components.websocket_api import event_message
from homeassistant.const import CONF_ICON, CONF_ID, CONF_TYPE
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.nodered.number import CONF_VALUE

from . import NodeRedEntity
from .const import CONF_TEXT, EVENT_VALUE_CHANGE, NODERED_DISCOVERY_NEW, TEXT_ICON

CONF_MAX_LENGTH = "max_length"
CONF_MIN_LENGTH = "min_length"
CONF_MODE = "mode"
CONF_PATTERN = "pattern"
CONF_STATE = "state"

DEFAULT_MODE = "text"
DEFAULT_MAX_LENGTH = 100
DEFAULT_MIN_LENGTH = 0


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the text platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities, connection)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_TEXT),
        async_discover,
    )


async def _async_setup_entity(hass, config, async_add_entities, connection):
    """Set up the Node-RED text."""

    async_add_entities([NodeRedText(hass, config, connection)])


class NodeRedText(NodeRedEntity, RestoreText):
    """Node-RED text class."""

    _bidirectional = True
    _component = CONF_TEXT

    def __init__(self, hass, config, connection):
        """Initialize the number."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

    async def async_added_to_hass(self) -> None:
        """Restore native_*."""
        await super().async_added_to_hass()
        if (last_text_data := await self.async_get_last_text_data()) is None:
            return
        self._attr_native_max = last_text_data.native_max
        self._attr_native_min = last_text_data.native_min
        self._attr_native_value = last_text_data.native_value

    async def async_set_value(self, value: str) -> None:
        """Set new value."""
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: value}
            )
        )

    def update_entity_state_attributes(self, msg):
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_native_value = msg.get(CONF_STATE)

    def update_discovery_config(self, msg):
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = self._config.get(CONF_ICON, TEXT_ICON)
        self._attr_native_min = self._config.get(CONF_MIN_LENGTH, DEFAULT_MIN_LENGTH)
        self._attr_native_max = self._config.get(CONF_MAX_LENGTH, DEFAULT_MAX_LENGTH)
        self._attr_pattern = self._config.get(CONF_PATTERN, None)
        self._attr_mode = TextMode(self._config.get(CONF_MODE, DEFAULT_MODE))
