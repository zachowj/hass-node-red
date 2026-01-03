"""Button platform for nodered."""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BUTTON, NODERED_DISCOVERY_NEW
from .entity import NodeRedEntity

_LOGGER = logging.getLogger(__name__)
EVENT_TRIGGER_NODE = "automation_triggered"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button platform."""

    async def async_discover(
        config: dict[str, Any], connection: ActiveConnection
    ) -> None:
        await _async_setup_entity(hass, config, async_add_entities, connection)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            NODERED_DISCOVERY_NEW.format(CONF_BUTTON),
            async_discover,
        )
    )


async def _async_setup_entity(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    connection: ActiveConnection,
) -> None:
    """Set up the Node-RED button."""
    async_add_entities([NodeRedButton(hass, config, connection)])


class NodeRedButton(NodeRedEntity, ButtonEntity):
    """Node-RED button class."""

    _bidirectional = True
    component = CONF_BUTTON

    def __init__(
        self, hass: HomeAssistant, config: dict[str, Any], connection: ActiveConnection
    ) -> None:
        """Initialize the button."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

    def press(self) -> None:
        """Handle the button press."""
        self._connection.send_message(
            event_message(
                self._message_id,
                {
                    CONF_TYPE: EVENT_TRIGGER_NODE,
                    "data": {
                        "entity": self.hass.states.get(self.entity_id),
                    },
                },
            )
        )
