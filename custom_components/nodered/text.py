"""Sensor platform for nodered."""

import logging
from typing import Any

from homeassistant.components.text import RestoreText, TextMode
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON, CONF_ID, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TEXT,
    EVENT_VALUE_CHANGE,
    HA_MAX_STATE_LENGTH,
    NODERED_DISCOVERY_NEW,
    TEXT_ICON,
)
from .entity import NodeRedEntity
from .number import CONF_VALUE

CONF_MAX_LENGTH = "max_length"
CONF_MIN_LENGTH = "min_length"
CONF_MODE = "mode"
CONF_PATTERN = "pattern"
CONF_STATE = "state"

DEFAULT_MODE = "text"
DEFAULT_MAX_LENGTH = 100
DEFAULT_MIN_LENGTH = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the text platform."""

    async def async_discover(
        config: dict[str, Any], connection: ActiveConnection
    ) -> None:
        await _async_setup_entity(hass, config, async_add_entities, connection)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            NODERED_DISCOVERY_NEW.format(CONF_TEXT),
            async_discover,
        )
    )


async def _async_setup_entity(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    connection: ActiveConnection,
) -> None:
    """Set up the Node-RED text."""
    async_add_entities([NodeRedText(hass, config, connection)])


class NodeRedText(NodeRedEntity, RestoreText):
    """Node-RED text class."""

    _bidirectional = True
    component = CONF_TEXT

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        connection: ActiveConnection,
    ) -> None:
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

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        # Ensure native value is a string for Text entity to avoid type
        # errors in Home Assistant when measuring value length.
        state = msg.get(CONF_STATE)
        value = str(state) if state is not None else None

        if value is not None:
            # Determine max length to enforce. Prefer the attribute if set,
            # otherwise fall back to the configured value or default.
            max_len = getattr(self, "_attr_native_max", None)
            if max_len is None:
                max_len = self._config.get(CONF_MAX_LENGTH, DEFAULT_MAX_LENGTH)

            # Enforce Home Assistant's maximum state length
            if isinstance(max_len, int) and max_len >= 0:
                effective_max = min(max_len, HA_MAX_STATE_LENGTH)
            else:
                effective_max = HA_MAX_STATE_LENGTH

            if len(value) > effective_max:
                _LOGGER.warning(
                    "Truncating text entity %s (node ID: %s) value to max length %s",
                    self.entity_id,
                    self._node_id,
                    effective_max,
                )
                value = value[:effective_max]

        self._attr_native_value = value

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = self._config.get(CONF_ICON, TEXT_ICON)
        self._attr_native_min = self._config.get(CONF_MIN_LENGTH, DEFAULT_MIN_LENGTH)
        cfg_max = self._config.get(CONF_MAX_LENGTH, DEFAULT_MAX_LENGTH)
        if isinstance(cfg_max, int) and cfg_max >= 0:
            self._attr_native_max = min(cfg_max, HA_MAX_STATE_LENGTH)
        else:
            self._attr_native_max = DEFAULT_MAX_LENGTH
        self._attr_pattern = self._config.get(CONF_PATTERN, None)
        self._attr_mode = TextMode(self._config.get(CONF_MODE, DEFAULT_MODE))
