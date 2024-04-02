"""Sensor platform for nodered."""
import logging

from homeassistant.components.number import RestoreNumber
from homeassistant.components.number.const import (
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_STEP,
    NumberMode,
)
from homeassistant.components.websocket_api import event_message
from homeassistant.const import (
    CONF_ICON,
    CONF_ID,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import NodeRedEntity
from .const import CONF_NUMBER, EVENT_VALUE_CHANGE, NODERED_DISCOVERY_NEW, NUMBER_ICON

_LOGGER = logging.getLogger(__name__)

CONF_MIN_VALUE = "min_value"
CONF_MAX_VALUE = "max_value"
CONF_STEP_VALUE = "step_value"
CONF_MODE = "mode"

CONF_STATE = "state"
CONF_VALUE = "value"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the number platform."""

    async def async_discover(config, connection):
        await _async_setup_entity(hass, config, async_add_entities, connection)

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_NUMBER),
        async_discover,
    )


async def _async_setup_entity(hass, config, async_add_entities, connection):
    """Set up the Node-RED number."""

    async_add_entities([NodeRedNumber(hass, config, connection)])


class NodeRedNumber(NodeRedEntity, RestoreNumber):
    """Node-RED number class."""

    _attr_native_min_value = DEFAULT_MIN_VALUE
    _attr_native_max_value = DEFAULT_MAX_VALUE
    _attr_native_step = DEFAULT_STEP
    _attr_native_value = 0
    _attr_mode = NumberMode.AUTO
    _bidirectional = True
    _component = CONF_NUMBER

    def __init__(self, hass, config, connection):
        """Initialize the number."""
        super().__init__(hass, config)
        self._message_id = config[CONF_ID]
        self._connection = connection

        self._attr_icon = self._config.get(CONF_ICON, NUMBER_ICON)
        self._attr_native_value = config.get(CONF_STATE)

        self._attr_native_min_value = self._config.get(
            CONF_MIN_VALUE, DEFAULT_MIN_VALUE
        )
        self._attr_native_max_value = self._config.get(
            CONF_MAX_VALUE, DEFAULT_MAX_VALUE
        )
        self._attr_native_step = self._config.get(CONF_STEP_VALUE, DEFAULT_STEP)
        self._attr_mode = self._config.get(CONF_MODE, NumberMode.AUTO)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self._connection.send_message(
            event_message(
                self._message_id, {CONF_TYPE: EVENT_VALUE_CHANGE, CONF_VALUE: value}
            )
        )

    async def async_added_to_hass(self) -> None:
        """Load the last known state when added to hass."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and (
            last_number_data := await self.async_get_last_number_data()
        ):
            if last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                self._attr_native_value = last_number_data.native_value

    def update_entity_state_attributes(self, msg):
        """Update the entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_native_value = msg.get(CONF_STATE)

    def update_discovery_config(self, msg):
        """Update the entity config."""
        super().update_discovery_config(msg)

        self._attr_icon = self._config.get(CONF_ICON, NUMBER_ICON)
        self._attr_native_min_value = self._config.get(
            CONF_MIN_VALUE, DEFAULT_MIN_VALUE
        )
        self._attr_native_max_value = self._config.get(
            CONF_MAX_VALUE, DEFAULT_MAX_VALUE
        )
        self._attr_native_step = self._config.get(CONF_STEP_VALUE, DEFAULT_STEP)
        self._attr_mode = self._config.get(CONF_MODE, NumberMode.AUTO)
        self._attr_native_unit_of_measurement = self._config.get(
            CONF_UNIT_OF_MEASUREMENT
        )
