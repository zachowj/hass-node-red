"""Support for Node-RED discovery."""

import logging
from typing import Any

from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

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
    NODERED_DISCOVERY,
    NODERED_DISCOVERY_NEW,
    NODERED_DISCOVERY_UPDATED,
)

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
DISCOVERY_DISPATCHED = "discovery_dispatched"


async def start_discovery(hass: HomeAssistant, hass_config: dict) -> None:
    """Initialize of Node-RED Discovery."""

    async def async_device_message_received(
        msg: dict[str, Any], connection: ActiveConnection
    ) -> None:
        """Process the received message."""
        component = msg[CONF_COMPONENT]
        server_id = msg[CONF_SERVER_ID]
        node_id = msg[CONF_NODE_ID]

        if component not in SUPPORTED_COMPONENTS:
            _LOGGER.warning("Integration %s is not supported", component)
            return

        discovery_hash = f"{DOMAIN}-{server_id}-{node_id}"
        data = hass_config

        _LOGGER.debug("Discovery message: %s", msg)

        if ALREADY_DISCOVERED not in data:
            data[ALREADY_DISCOVERED] = set()

        # Check if already discovered
        already_discovered = discovery_hash in data[ALREADY_DISCOVERED]

        if already_discovered:
            log_text = "Removing" if CONF_REMOVE in msg else "Updating"

            _LOGGER.info("%s %s %s %s", log_text, component, server_id, node_id)

            async_dispatcher_send(
                hass, NODERED_DISCOVERY_UPDATED.format(discovery_hash), msg, connection
            )
        else:
            # Add component - ensure platform is set up first
            _LOGGER.info("Creating %s %s %s", component, server_id, node_id)

            data[ALREADY_DISCOVERED].add(discovery_hash)

            async_dispatcher_send(
                hass, NODERED_DISCOVERY_NEW.format(component), msg, connection
            )

    hass.data[DOMAIN_DATA][DISCOVERY_DISPATCHED] = async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY,
        async_device_message_received,
    )


def stop_discovery(hass: HomeAssistant) -> None:
    """Remove discovery dispatcher."""
    hass.data[DOMAIN_DATA][DISCOVERY_DISPATCHED]()
