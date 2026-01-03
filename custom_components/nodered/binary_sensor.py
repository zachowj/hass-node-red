"""Binary sensor platform for nodered."""

from numbers import Number
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_STATE, STATE_HOME, STATE_ON, STATE_OPEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BINARY_SENSOR, NODERED_DISCOVERY_NEW
from .entity import NodeRedEntity

try:
    from homeassistant.components.lock.const import LockState

    STATE_UNLOCKED = LockState.UNLOCKED
except ImportError:
    # Fallback for older Home Assistant versions
    STATE_UNLOCKED = "unlocked"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""

    async def async_discover(
        config: dict[str, Any], _connection: ActiveConnection
    ) -> None:
        await _async_setup_entity(hass, config, async_add_devices)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            NODERED_DISCOVERY_NEW.format(CONF_BINARY_SENSOR),
            async_discover,
        )
    )


async def _async_setup_entity(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the Node-RED binary-sensor."""
    async_add_devices([NodeRedBinarySensor(hass, config)])


class NodeRedBinarySensor(NodeRedEntity, BinarySensorEntity):
    """Node-RED binary-sensor class."""

    on_states = (
        "1",
        "true",
        "yes",
        "enable",
        STATE_ON,
        STATE_OPEN,
        STATE_HOME,
        STATE_UNLOCKED,
    )
    component = CONF_BINARY_SENSOR

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the binary sensor."""
        super().__init__(hass, config)
        self._attr_is_on = self._evaluate_sensor_state(config.get(CONF_STATE))

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Update entity state attributes."""
        super().update_entity_state_attributes(msg)
        self._attr_is_on = self._evaluate_sensor_state(msg.get(CONF_STATE))

    def _evaluate_sensor_state(self, value: Any) -> Any:
        """Parse state."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.lower().strip()
            if value in NodeRedBinarySensor.on_states:
                return True
        elif isinstance(value, Number):
            return value != 0

        return False
