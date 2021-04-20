"""Sensor platform for nodered."""
import json
import logging

import voluptuous as vol

from homeassistant.components.websocket_api import event_message
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_ID,
    CONF_STATE,
    CONF_TYPE,
    EVENT_STATE_CHANGED,
)
from homeassistant.core import callback
from homeassistant.helpers import entity_platform, trigger
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import ToggleEntity

from . import NodeRedEntity
from .const import (
    CONF_CONFIG,
    CONF_DATA,
    CONF_DEVICE_TRIGGER,
    CONF_OUTPUT_PATH,
    CONF_PAYLOAD,
    CONF_REMOVE,
    CONF_SKIP_CONDITION,
    CONF_SUB_TYPE,
    CONF_SWITCH,
    CONF_TRIGGER_ENTITY_ID,
    DOMAIN,
    NODERED_DISCOVERY_NEW,
    SERVICE_TRIGGER,
    SWITCH_ICON,
)
from .utils import NodeRedJSONEncoder

_LOGGER = logging.getLogger(__name__)

SERVICE_TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_ids,
        vol.Optional(CONF_TRIGGER_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_SKIP_CONDITION): cv.boolean,
        vol.Optional(CONF_OUTPUT_PATH): cv.boolean,
        vol.Optional(CONF_PAYLOAD): vol.Extra,
    }
)
EVENT_TRIGGER_NODE = "automation_triggered"
EVENT_DEVICE_TRIGGER = "device_trigger"

TYPE_SWITCH = "switch"
TYPE_DEVICE_TRIGGER = "device_trigger"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Switch platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities, connection)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_SWITCH),
        async_discover,
    )

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_TRIGGER, SERVICE_TRIGGER_SCHEMA, "async_trigger_node"
    )


async def _async_setup_entity(hass, config, async_add_entities, connection):
    """Set up the Node-RED Switch."""

    switch_type = config.get(CONF_SUB_TYPE, TYPE_SWITCH)
    switch_class = (
        NodeRedDeviceTrigger if switch_type == TYPE_DEVICE_TRIGGER else NodeRedSwitch
    )
    async_add_entities([switch_class(hass, config, connection)])


class NodeRedSwitch(ToggleEntity, NodeRedEntity):
    """Node-RED Switch class."""

    def __init__(self, hass, config, connection):
        """Initialize the switch."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection
        self._state = config.get(CONF_STATE, True)
        self._component = CONF_SWITCH
        self._available = True

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._config.get(CONF_ICON, SWITCH_ICON)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        self._update_node_red(False)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        self._update_node_red(True)

    async def async_trigger_node(self, **kwargs) -> None:
        """Trigger node in Node-RED."""
        data = {}
        data[CONF_ENTITY_ID] = kwargs.get(CONF_TRIGGER_ENTITY_ID)
        data[CONF_SKIP_CONDITION] = kwargs.get(CONF_SKIP_CONDITION, False)
        data[CONF_OUTPUT_PATH] = kwargs.get(CONF_OUTPUT_PATH, True)
        if kwargs.get(CONF_PAYLOAD) is not None:
            data[CONF_PAYLOAD] = kwargs[CONF_PAYLOAD]

        self._connection.send_message(
            event_message(
                self._message_id,
                {CONF_TYPE: EVENT_TRIGGER_NODE, CONF_DATA: data},
            )
        )

    def _update_node_red(self, state):
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_STATE_CHANGED, CONF_STATE: state}
            )
        )

    @callback
    def handle_lost_connection(self):
        """Set availability to False when disconnected."""
        self._available = False
        self.async_write_ha_state()

    @callback
    def handle_discovery_update(self, msg, connection):
        """Update entity config."""
        if CONF_REMOVE in msg:
            # Remove entity
            self.hass.async_create_task(self.async_remove())
        else:
            self._available = True
            self._state = msg[CONF_STATE]
            self._config = msg[CONF_CONFIG]
            self._message_id = msg[CONF_ID]
            self._connection = connection
            self._connection.subscriptions[msg[CONF_ID]] = self.handle_lost_connection
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        self._connection.subscriptions[self._message_id] = self.handle_lost_connection


class NodeRedDeviceTrigger(NodeRedSwitch):
    """Node-RED Device Trigger class."""

    def __init__(self, hass, config, connection):
        """Initialize the switch."""
        super().__init__(hass, config, connection)
        self._trigger_config = config[CONF_DEVICE_TRIGGER]
        self._unsubscribe_device_trigger = None

    @callback
    def handle_lost_connection(self):
        """Set remove device trigger when disconnected."""
        super().handle_lost_connection()
        self.remove_device_trigger()

    async def add_device_trigger(self):
        """Validate device trigger."""

        @callback
        def forward_trigger(event, context=None):
            """Forward events to websocket."""
            message = event_message(
                self._message_id,
                {"type": EVENT_DEVICE_TRIGGER, "data": event["trigger"]},
            )
            self._connection.send_message(
                json.dumps(message, cls=NodeRedJSONEncoder, allow_nan=False)
            )

        try:
            trigger_config = await trigger.async_validate_trigger_config(
                self.hass, [self._trigger_config]
            )
            self._unsubscribe_device_trigger = await trigger.async_initialize_triggers(
                self.hass,
                trigger_config,
                forward_trigger,
                DOMAIN,
                DOMAIN,
                _LOGGER.log,
            )
        except vol.MultipleInvalid as ex:
            _LOGGER.error(
                f"Error initializing device trigger '{self._node_id}': {str(ex)}",
            )

    def remove_device_trigger(self):
        """Remove device trigger."""
        self._trigger_config = None
        if self._unsubscribe_device_trigger is not None:
            _LOGGER.info(f"removed device triger - {self._server_id} {self._node_id}")
            self._unsubscribe_device_trigger()
            self._unsubscribe_device_trigger = None

    @callback
    async def handle_discovery_update(self, msg, connection):
        """Update entity config."""
        if CONF_REMOVE not in msg and self._trigger_config != msg[CONF_DEVICE_TRIGGER]:
            self.remove_device_trigger()
            self._trigger_config = msg[CONF_DEVICE_TRIGGER]
            await self.add_device_trigger()

        super().handle_discovery_update(msg, connection)

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        await self.add_device_trigger()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.remove_device_trigger()
        await super().async_will_remove_from_hass()
