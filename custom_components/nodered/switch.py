"""Switch platform for nodered."""

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.websocket_api import event_message
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_ID,
    CONF_STATE,
    CONF_TYPE,
    EVENT_STATE_CHANGED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.nodered.config_flow import NodeRedConfigEntry

from . import NodeRedEntity
from .const import (
    CONF_CONFIG,
    CONF_DATA,
    CONF_MESSAGE,
    CONF_OUTPUT_PATH,
    CONF_SWITCH,
    NODERED_DISCOVERY_NEW,
    SERVICE_TRIGGER,
    SWITCH_ICON,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_TRIGGER_SCHEMA = {
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_OUTPUT_PATH, default="0"): cv.string,
    vol.Optional(CONF_MESSAGE, default={}): dict,
}

EVENT_TRIGGER_NODE = "automation_triggered"
EVENT_DEVICE_TRIGGER = "device_trigger"

TYPE_SWITCH = "switch"
TYPE_DEVICE_TRIGGER = "device_trigger"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NodeRedConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Switch platform."""

    async def async_discover(
        config: NodeRedConfigEntry, connection: ActiveConnection
    ) -> None:
        await _async_setup_entity(hass, config, async_add_entities, connection)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            NODERED_DISCOVERY_NEW.format(CONF_SWITCH),
            async_discover,
        )
    )

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_TRIGGER, SERVICE_TRIGGER_SCHEMA, "async_trigger_node"
    )


async def _async_setup_entity(
    hass: HomeAssistant,
    config: NodeRedConfigEntry,
    async_add_entities: AddEntitiesCallback,
    connection: ActiveConnection,
) -> None:
    """Set up the Node-RED Switch."""
    async_add_entities([NodeRedSwitch(hass, config, connection)])


class NodeRedSwitch(NodeRedEntity, ToggleEntity):
    """Node-RED Switch class."""

    _component = CONF_SWITCH
    _bidirectional = True

    def __init__(
        self,
        hass: HomeAssistant,
        config: NodeRedConfigEntry,
        connection: ActiveConnection,
    ) -> None:
        """Initialize the switch."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

        self._attr_state = config.get(CONF_STATE, True)
        self._attr_icon = self._config.get(CONF_ICON)

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return self._attr_state

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        self._update_node_red(state=False)

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        self._update_node_red(state=True)

    async def async_trigger_node(self, **kwargs: object) -> None:
        """Trigger node in Node-RED."""
        data = {}
        data[CONF_OUTPUT_PATH] = kwargs.get(CONF_OUTPUT_PATH, True)
        if kwargs.get(CONF_MESSAGE) is not None:
            data[CONF_MESSAGE] = kwargs[CONF_MESSAGE]

        self._connection.send_message(
            event_message(
                self._message_id,
                {CONF_TYPE: EVENT_TRIGGER_NODE, CONF_DATA: data},
            )
        )

    def _update_node_red(self, state: str) -> None:
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_STATE_CHANGED, CONF_STATE: state}
            )
        )

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_state = msg.get(CONF_STATE)

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Update the entity config."""
        super().update_discovery_config(msg)
        self._attr_icon = msg[CONF_CONFIG].get(CONF_ICON, SWITCH_ICON)
