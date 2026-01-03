"""Node-RED base entity class."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_registry import async_get

if TYPE_CHECKING:
    from homeassistant.components.websocket_api.connection import ActiveConnection

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
    DOMAIN,
    DOMAIN_DATA,
    NODERED_CONFIG_UPDATE,
    NODERED_DISCOVERY,
    NODERED_DISCOVERY_UPDATED,
    NODERED_ENTITY,
)
from .discovery import ALREADY_DISCOVERED, CHANGE_ENTITY_TYPE


class MissingConfigError(TypeError):
    """Raised when config is missing required values."""


class NodeRedEntity(Entity):
    """Base entity for Node-RED integration."""

    component: ClassVar[str] = ""
    _bidirectional = False

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the entity."""
        if not type(self).component:
            msg = f"{type(self).__name__} must set class attribute `component`"
            raise TypeError(msg)
        self.hass = hass
        self._server_id = config.get(CONF_SERVER_ID)
        self._node_id = config.get(CONF_NODE_ID)
        if self._server_id is None or self._node_id is None:
            msg = f"{type(self).__name__} requires 'server_id' and 'node_id'"
            raise MissingConfigError(msg)
        self._attr_unique_id = f"{DOMAIN}-{self._server_id}-{self._node_id}"
        self._attr_should_poll = False

        device_info = config.get(CONF_DEVICE_INFO, {})
        device_id = device_info.get("id")
        if device_id:
            self._attr_device_info = DeviceInfo(
                identifiers=generate_device_identifiers(device_id),
                hw_version=device_info.get("hw_version"),
                manufacturer=device_info.get("manufacturer"),
                model=device_info.get("model"),
                name=device_info.get("name"),
                sw_version=device_info.get("sw_version"),
            )
        else:
            self._attr_device_info = None

        self.update_discovery_config(config)
        self.update_entity_state_attributes(config)

    @callback
    def handle_config_update(self, msg: dict[str, Any]) -> None:
        """Handle an incoming config update and write state."""
        self.update_config(msg)
        self.async_write_ha_state()

    @callback
    def handle_entity_update(self, msg: dict[str, Any]) -> None:
        """Update entity state attributes and write state."""
        self.update_entity_state_attributes(msg)
        self.async_write_ha_state()

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Set extra state attributes from incoming message."""
        self._attr_extra_state_attributes = msg.get(CONF_ATTRIBUTES, {})

    @callback
    def handle_lost_connection(self) -> None:
        """Mark entity unavailable after losing connection."""
        self._attr_available = False
        self.async_write_ha_state()

    @callback
    def handle_discovery_update(
        self, msg: dict[str, Any], connection: ActiveConnection
    ) -> None:
        """Update entity config/state based on discovery message."""
        if CONF_REMOVE in msg:
            if msg[CONF_REMOVE] == CHANGE_ENTITY_TYPE:

                @callback
                def recreate_entity() -> None:
                    del msg[CONF_REMOVE]
                    async_dispatcher_send(
                        self.hass,
                        NODERED_DISCOVERY.format(msg[CONF_COMPONENT]),
                        msg,
                        connection,
                    )

                self.async_on_remove(recreate_entity)
                # Schedule entity removal; recreation will happen when the on_remove
                # callback runs and re-dispatches discovery for the new entity
                self.hass.async_create_task(self.async_remove())
            else:

                @callback
                def cleanup_discovery() -> None:
                    """Remove discovery tracking for this entity, if present."""
                    with suppress(KeyError):
                        del self.hass.data[DOMAIN_DATA][ALREADY_DISCOVERED][
                            self.unique_id
                        ]

                self.async_on_remove(cleanup_discovery)

            return

        self.update_discovery_device_info(msg)
        if CONF_CONFIG in msg:
            self.update_discovery_config(msg)

        # Bidirectional subscription handling
        if self._bidirectional and "id" in msg:
            self._attr_available = True
            self._message_id = msg["id"]
            self._connection = connection
            self._connection.subscriptions[msg["id"]] = self.handle_lost_connection

        self.async_write_ha_state()

    def entity_category_mapper(self, category: str) -> None | EntityCategory:
        """Map Node-RED category strings to Home Assistant EntityCategory."""
        if category == "config":
            return EntityCategory.CONFIG
        if category == "diagnostic":
            return EntityCategory.DIAGNOSTIC
        return None

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Apply discovery config fields to the entity attributes."""
        self._config = msg[CONF_CONFIG]
        self._attr_icon = self._config.get(CONF_ICON)
        self._attr_name = self._config.get(CONF_NAME, f"{DOMAIN} {self._node_id}")
        self._attr_device_class = self._config.get(CONF_DEVICE_CLASS)
        self._attr_entity_category = self.entity_category_mapper(
            self._config.get(CONF_ENTITY_CATEGORY)
        )
        self._attr_entity_picture = self._config.get(CONF_ENTITY_PICTURE)
        self._attr_unit_of_measurement = self._config.get(CONF_UNIT_OF_MEASUREMENT)

    def update_config(self, msg: dict[str, Any]) -> None:
        """Apply runtime config updates to the entity."""
        config = msg.get(CONF_CONFIG, {})

        if config.get(CONF_NAME):
            self._attr_name = config.get(CONF_NAME)
        if config.get(CONF_ICON):
            self._attr_icon = config.get(CONF_ICON)
        if config.get(CONF_ENTITY_PICTURE):
            self._attr_entity_picture = config.get(CONF_ENTITY_PICTURE)
        if config.get(CONF_OPTIONS):
            self._attr_options = config.get(CONF_OPTIONS)

    def update_discovery_device_info(self, msg: dict[str, Any]) -> None:
        """Update or remove device info for this entity based on discovery msg."""
        entity_registry = async_get(self.hass)
        if self.unique_id is None:
            raise RuntimeError("unique_id should be set during initialization")
        entity_id = entity_registry.async_get_entity_id(
            self.component,
            DOMAIN,
            self.unique_id,
        )
        device_info = msg.get(CONF_DEVICE_INFO)

        # Exit early when there is no device info. If an entity existed, dissociate it from any device.
        if device_info is None:
            if entity_id is not None:
                entity_registry.async_update_entity(entity_id, device_id=None)
            return

        device_registry = dr.async_get(self.hass)
        identifiers = generate_device_identifiers(device_info["id"])

        # Get or create the device
        device = device_registry.async_get_or_create(
            config_entry_id=self.hass.config_entries.async_entries(DOMAIN)[0].entry_id,
            identifiers=identifiers,
            name=device_info.get("name"),
            manufacturer=device_info.get("manufacturer"),
            model=device_info.get("model"),
        )

        # Update device properties
        device_registry.async_update_device(
            device_id=device.id,
            hw_version=device_info.get("hw_version"),
            name=device_info.get("name"),
            manufacturer=device_info.get("manufacturer"),
            model=device_info.get("model"),
            sw_version=device_info.get("sw_version"),
        )

        # Associate entity with device
        if entity_id is not None:
            entity_registry.async_update_entity(entity_id, device_id=device.id)

    async def async_added_to_hass(self) -> None:
        """Register dispatcher listeners when added to Home Assistant."""
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

    async def async_will_remove_from_hass(self) -> None:
        """Remove dispatcher listeners when the entity is removed from hass."""
        if self._remove_signal_entity_update is not None:
            self._remove_signal_entity_update()
        if self._remove_signal_discovery_update is not None:
            self._remove_signal_discovery_update()
        if self._remove_signal_config_update is not None:
            self._remove_signal_config_update()


def generate_device_identifiers(device_id: str) -> set[tuple[str, str]]:
    """Create identifiers set from device info."""
    return {(DOMAIN, device_id)}
