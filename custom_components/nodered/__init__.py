"""
Component to integrate with node-red.

For more details about this component, please refer to
https://github.com/zachowj/hass-node-red
"""
import asyncio
import logging
from typing import Any, Dict, Optional, Union

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_STATE,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_COMPONENT,
    CONF_CONFIG,
    CONF_DEVICE_INFO,
    CONF_NAME,
    CONF_NODE_ID,
    CONF_REMOVE,
    CONF_SERVER_ID,
    CONF_VERSION,
    DOMAIN,
    DOMAIN_DATA,
    NAME,
    NODERED_DISCOVERY_UPDATED,
    NODERED_ENTITY,
    STARTUP_MESSAGE,
    VERSION,
)
from .discovery import (
    ALREADY_DISCOVERED,
    CHANGE_ENTITY_TYPE,
    CONFIG_ENTRY_IS_SETUP,
    NODERED_DISCOVERY,
    start_discovery,
    stop_discovery,
)
from .websocket import register_websocket_handlers

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN_DATA) is None:
        hass.data.setdefault(DOMAIN_DATA, {})
        _LOGGER.info(STARTUP_MESSAGE)

    register_websocket_handlers(hass)
    await start_discovery(hass, hass.data[DOMAIN_DATA], entry)
    hass.bus.async_fire(DOMAIN, {CONF_TYPE: "loaded", CONF_VERSION: VERSION})

    entry.add_update_listener(async_reload_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in hass.data[DOMAIN_DATA][CONFIG_ENTRY_IS_SETUP]
            ]
        )
    )

    if unloaded:
        stop_discovery(hass)
        hass.data.pop(DOMAIN_DATA)
        hass.bus.async_fire(DOMAIN, {CONF_TYPE: "unloaded"})

    return unloaded


class NodeRedEntity(Entity):
    """nodered Sensor class."""

    def __init__(self, hass, config):
        """Initialize the entity."""
        self.hass = hass
        self.attr = {}
        self._config = config[CONF_CONFIG]
        self._component = None
        self._device_info = config.get(CONF_DEVICE_INFO)
        self._state = None
        self._server_id = config[CONF_SERVER_ID]
        self._node_id = config[CONF_NODE_ID]
        self._remove_signal_discovery_update = None
        self._remove_signal_entity_update = None

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state.

        False if entity pushes its state to HA.
        """
        return False

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}-{self._server_id}-{self._node_id}"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this binary_sensor."""
        return self._config.get(CONF_DEVICE_CLASS)

    @property
    def name(self) -> Optional[str]:
        """Return the name of the sensor."""
        return self._config.get(CONF_NAME, f"{NAME} {self._node_id}")

    @property
    def state(self) -> Union[None, str, int, float]:
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> Optional[str]:
        """Return the icon of the sensor."""
        return self._config.get(CONF_ICON)

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit this state is expressed in."""
        return self._config.get(CONF_UNIT_OF_MEASUREMENT)

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes."""
        return self.attr

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """Return device specific attributes."""
        info = None
        if self._device_info is not None and "id" in self._device_info:
            # Use the id property to create the device identifier then delete it
            info = {"identifiers": {(DOMAIN, self._device_info["id"])}}
            del self._device_info["id"]
            info.update(self._device_info)

        return info

    @callback
    def handle_entity_update(self, msg):
        """Update entity state."""
        _LOGGER.debug(f"Entity Update: {msg}")
        self.attr = msg.get("attributes", {})
        self._state = msg[CONF_STATE]
        self.async_write_ha_state()

    @callback
    def handle_discovery_update(self, msg, connection):
        """Update entity config."""
        if CONF_REMOVE not in msg:
            self._config = msg[CONF_CONFIG]
            self.async_write_ha_state()
            return

        # Otherwise, remove entity
        if msg[CONF_REMOVE] == CHANGE_ENTITY_TYPE:
            # recreate entity if component type changed
            @callback
            def recreate_entity():
                """Create entity with new type."""
                del msg[CONF_REMOVE]
                async_dispatcher_send(
                    self.hass,
                    NODERED_DISCOVERY.format(msg[CONF_COMPONENT]),
                    msg,
                    connection,
                )

            self.async_on_remove(recreate_entity)

        self.hass.async_create_task(self.async_remove())

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""

        self._remove_signal_entity_update = async_dispatcher_connect(
            self.hass,
            NODERED_ENTITY.format(self._server_id, self._node_id),
            self.handle_entity_update,
        )
        self._remove_signal_discovery_update = async_dispatcher_connect(
            self.hass,
            NODERED_DISCOVERY_UPDATED.format(self.unique_id),
            self.handle_discovery_update,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._remove_signal_entity_update is not None:
            self._remove_signal_entity_update()
        if self._remove_signal_discovery_update is not None:
            self._remove_signal_discovery_update()

        del self.hass.data[DOMAIN_DATA][ALREADY_DISCOVERED][self.unique_id]

        # Remove the entity_id from the entity registry
        registry = await self.hass.helpers.entity_registry.async_get_registry()
        entity_id = registry.async_get_entity_id(
            self._component,
            DOMAIN,
            self.unique_id,
        )
        if entity_id:
            registry.async_remove(entity_id)
            _LOGGER.info(f"Entity removed: {entity_id}")


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
