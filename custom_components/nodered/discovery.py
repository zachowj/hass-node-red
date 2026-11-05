"""Support for Node-RED discovery."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .const import (
    CONF_BINARY_SENSOR,
    CONF_BUTTON,
    CONF_COMPONENT,
    CONF_NODE_ID,
    CONF_NUMBER,
    CONF_REMOVE,
    CONF_SELECT,
    CONF_SENSOR,
    CONF_SERVER_ID,
    CONF_SWITCH,
    CONF_TEXT,
    CONF_TIME,
    DOMAIN,
    DOMAIN_DATA,
)

if TYPE_CHECKING:
    from homeassistant.components.websocket_api.connection import ActiveConnection

    from .entity import NodeRedEntity

SUPPORTED_COMPONENTS = [
    CONF_BINARY_SENSOR,
    CONF_BUTTON,
    CONF_NUMBER,
    CONF_SELECT,
    CONF_SENSOR,
    CONF_SWITCH,
    CONF_TEXT,
    CONF_TIME,
]

_LOGGER = logging.getLogger(__name__)

ALREADY_DISCOVERED = "already_discovered"
CHANGE_ENTITY_TYPE = "change_entity_type"
PLATFORMS_LOADED = "platforms_loaded"
DISCOVERY_PLATFORMS = "discovery_platforms"
ENTITIES = "entities"

type DiscoverCallback = Callable[[dict[str, Any], ActiveConnection], None]


def discovery_hash(server_id: str, node_id: str) -> str:
    """Return the hash identifying a Node-RED node's entity."""
    return f"{DOMAIN}-{server_id}-{node_id}"


@callback
def async_register_platform(
    hass: HomeAssistant, component: str, discover: DiscoverCallback
) -> CALLBACK_TYPE:
    """Register the callback that creates a component's entities."""
    platforms = hass.data[DOMAIN_DATA].setdefault(DISCOVERY_PLATFORMS, {})
    platforms[component] = discover

    @callback
    def unregister() -> None:
        platforms.pop(component, None)

    return unregister


@callback
def async_register_entity(hass: HomeAssistant, entity: NodeRedEntity) -> None:
    """Route Node-RED messages for this entity's node to it."""
    entities = hass.data.setdefault(DOMAIN_DATA, {}).setdefault(ENTITIES, {})
    entities[entity.unique_id] = entity


@callback
def async_unregister_entity(hass: HomeAssistant, entity: NodeRedEntity) -> None:
    """Stop routing Node-RED messages to this entity."""
    entities = hass.data.get(DOMAIN_DATA, {}).get(ENTITIES, {})
    if entities.get(entity.unique_id) is entity:
        del entities[entity.unique_id]


@callback
def async_get_entity(
    hass: HomeAssistant, server_id: str, node_id: str
) -> NodeRedEntity | None:
    """Return the entity for a Node-RED node, if there is one."""
    entities = hass.data.get(DOMAIN_DATA, {}).get(ENTITIES, {})
    return entities.get(discovery_hash(server_id, node_id))


@callback
def async_discover(
    hass: HomeAssistant, msg: dict[str, Any], connection: ActiveConnection
) -> None:
    """Create or update the entity described by a discovery message."""
    if (data := hass.data.get(DOMAIN_DATA)) is None:
        return

    component = msg[CONF_COMPONENT]
    server_id = msg[CONF_SERVER_ID]
    node_id = msg[CONF_NODE_ID]

    if component not in SUPPORTED_COMPONENTS:
        _LOGGER.warning("Integration %s is not supported", component)
        return

    _LOGGER.debug("Discovery message: %s", msg)

    discovered = data.setdefault(ALREADY_DISCOVERED, set())
    unique_id = discovery_hash(server_id, node_id)

    if unique_id in discovered:
        log_text = "Removing" if CONF_REMOVE in msg else "Updating"
        _LOGGER.info("%s %s %s %s", log_text, component, server_id, node_id)

        if (entity := async_get_entity(hass, server_id, node_id)) is None:
            return
        try:
            entity.handle_discovery_update(msg, connection)
        except Exception:
            _LOGGER.exception("Error updating %s", entity.entity_id)
    else:
        _LOGGER.info("Creating %s %s %s", component, server_id, node_id)

        discovered.add(unique_id)

        if (discover := data.get(DISCOVERY_PLATFORMS, {}).get(component)) is None:
            return
        try:
            discover(msg, connection)
        except Exception:
            _LOGGER.exception("Error creating %s %s %s", component, server_id, node_id)
