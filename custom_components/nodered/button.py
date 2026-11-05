"""Button platform for nodered."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BUTTON
from .entity import NodeRedEntity, async_setup_discovery

_LOGGER = logging.getLogger(__name__)
EVENT_TRIGGER_NODE = "automation_triggered"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button platform."""

    async_setup_discovery(hass, config_entry, NodeRedButton, async_add_entities)


class NodeRedButton(NodeRedEntity, ButtonEntity):
    """Node-RED button class."""

    _bidirectional = True
    component = CONF_BUTTON

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
