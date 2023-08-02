"""
Component to integrate with node-red.

For more details about this component, please refer to
https://github.com/zachowj/hass-node-red
"""
import asyncio
import logging
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_ID,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.entity_registry import async_entries_for_device, async_get

from .const import (
    CONF_ATTRIBUTES,
    CONF_COMPONENT,
    CONF_CONFIG,
    CONF_DEVICE_INFO,
    CONF_ENTITY_PICTURE,
    CONF_NAME,
    CONF_NODE_ID,
    CONF_OPTIONS,
    CONF_REMOVE,
    CONF_SERVER_ID,
    CONF_VERSION,
    DOMAIN,
    DOMAIN_DATA,
    NODERED_CONFIG_UPDATE,
    NODERED_DISCOVERY_UPDATED,
    NODERED_ENTITY,
    STARTUP_MESSAGE,
)
from .discovery import (
    ALREADY_DISCOVERED,
    CHANGE_ENTITY_TYPE,
    CONFIG_ENTRY_IS_SETUP,
    NODERED_DISCOVERY,
    start_discovery,
    stop_discovery,
)
from .version import __version__ as VERSION
from .websocket import register_websocket_handlers

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN_DATA) is None:
        hass.data.setdefault(DOMAIN_DATA, {})
        _LOGGER.info(STARTUP_MESSAGE)

    register_websocket_handlers(hass)
    await start_discovery(hass, hass.data[DOMAIN_DATA], entry)
    hass.bus.async_fire(DOMAIN, {CONF_TYPE: "loaded", CONF_VERSION: VERSION})

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

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

    _component = None
    remove_signal_discovery_update = None
    remove_signal_entity_update = None
    _bidirectional = False

    def __init__(self, hass, config):
        """Initialize the entity."""
        self.hass = hass
        self._device_info = config.get(CONF_DEVICE_INFO)
        self._server_id = config[CONF_SERVER_ID]
        self._node_id = config[CONF_NODE_ID]
        self._attr_unique_id = f"{DOMAIN}-{self._server_id}-{self._node_id}"
        self._attr_should_poll = False

        self.update_discovery_config(config)
        self.update_entity_state_attributes(config)

    @property
    def device_info(self) -> Optional[dict[str, Any]]:
        """Return device specific attributes."""
        info = None
        if self._device_info is not None and "id" in self._device_info:
            # Use the id property to create the device identifier then delete it
            info = {"identifiers": {(DOMAIN, self._device_info["id"])}}
            del self._device_info["id"]
            info.update(self._device_info)

        return info

    @callback
    def handle_config_update(self, msg):
        """Handle config update."""
        self.update_config(msg)
        self.async_write_ha_state()

    @callback
    def handle_entity_update(self, msg):
        """Update entity state."""
        _LOGGER.debug(f"Entity Update: {msg}")
        self.update_entity_state_attributes(msg)
        self.async_write_ha_state()

    def update_entity_state_attributes(self, msg):
        """Update entity state attributes."""
        self._attr_extra_state_attributes = msg.get(CONF_ATTRIBUTES, {})

    @callback
    def handle_lost_connection(self):
        """Set availability to False when disconnected."""
        self._attr_available = False
        self.async_write_ha_state()

    @callback
    def handle_discovery_update(self, msg, connection):
        """Update entity config."""
        if CONF_REMOVE in msg:
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

            # Remove entity
            self.hass.async_create_task(self.async_remove(force_remove=True))
        else:
            self.update_discovery_config(msg)
            self.update_discovery_device_info(msg)

            if self._bidirectional:
                self._attr_available = True
                self._message_id = msg[CONF_ID]
                self._connection = connection
                self._connection.subscriptions[
                    msg[CONF_ID]
                ] = self.handle_lost_connection
            self.async_write_ha_state()

    def entity_category_mapper(self, category):
        """Map Node-RED category to Home Assistant entity category."""
        if category == "config":
            return EntityCategory.CONFIG
        if category == "diagnostic":
            return EntityCategory.DIAGNOSTIC
        return None

    def update_discovery_config(self, msg):
        """Update entity config."""
        self._config = msg[CONF_CONFIG]
        self._attr_icon = self._config.get(CONF_ICON)
        self._attr_name = self._config.get(CONF_NAME, f"{DOMAIN} {self._node_id}")
        self._attr_device_class = self._config.get(CONF_DEVICE_CLASS)
        self._attr_entity_category = self.entity_category_mapper(
            self._config.get(CONF_ENTITY_CATEGORY)
        )
        self._attr_entity_picture = self._config.get(CONF_ENTITY_PICTURE)
        self._attr_unit_of_measurement = self._config.get(CONF_UNIT_OF_MEASUREMENT)

    def update_config(self, msg):
        """Update entity config."""
        config = msg.get(CONF_CONFIG, {})

        if config.get(CONF_NAME):
            self._attr_name = config.get(CONF_NAME)
        if config.get(CONF_ICON):
            self._attr_icon = config.get(CONF_ICON)
        if config.get(CONF_ENTITY_PICTURE):
            self._attr_entity_picture = config.get(CONF_ENTITY_PICTURE)
        if config.get(CONF_OPTIONS):
            self._attr_options = config.get(CONF_OPTIONS)

    def update_discovery_device_info(self, msg):
        """Update entity device info."""
        entity_registry = async_get(self.hass)
        entity_id = entity_registry.async_get_entity_id(
            self._component,
            DOMAIN,
            self.unique_id,
        )
        self._device_info = msg.get(CONF_DEVICE_INFO)

        # Remove entity from device registry if device info is removed
        if self._device_info is None and entity_id is not None:
            entity_registry.async_update_entity(entity_id, device_id=None)

        # Update device info
        if self._device_info is not None:
            device_registry = dr.async_get(self.hass)
            device_info = self.device_info
            indentifiers = device_info.pop("identifiers")
            device = device_registry.async_get_device(indentifiers)
            if device is not None:
                device_registry.async_update_device(
                    device.id,
                    **device_info,
                )
                # add entity to device
                if entity_id is not None:
                    entity_registry.async_update_entity(entity_id, device_id=device.id)

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
        self._remove_signal_config_update = async_dispatcher_connect(
            self.hass,
            NODERED_CONFIG_UPDATE.format(self._server_id, self._node_id),
            self.handle_config_update,
        )

        if self._bidirectional:
            self._connection.subscriptions[
                self._message_id
            ] = self.handle_lost_connection

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._remove_signal_entity_update is not None:
            self._remove_signal_entity_update()
        if self._remove_signal_discovery_update is not None:
            self._remove_signal_discovery_update()

        del self.hass.data[DOMAIN_DATA][ALREADY_DISCOVERED][self.unique_id]

        # Remove the entity_id from the entity registry
        entity_registry = async_get(self.hass)
        entity_id = entity_registry.async_get_entity_id(
            self._component,
            DOMAIN,
            self.unique_id,
        )
        if entity_id:
            entity_registry.async_remove(entity_id)
            _LOGGER.info(f"Entity removed: {entity_id}")


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a entry from the device registry."""
    entity_registry = async_get(hass)
    entries = async_entries_for_device(entity_registry, device_entry.id)
    # Remove entities from device before removing device so the entities are not removed from HA
    if entries:
        for entry in entries:
            entity_registry.async_update_entity(entry.entity_id, device_id=None)

    return True
