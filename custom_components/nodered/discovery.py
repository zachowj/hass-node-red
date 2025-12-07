"""Support for Node-RED discovery."""

import asyncio
import logging

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
PLATFORM_SETUP_LOCK = "platform_setup_lock"
PLATFORMS_LOADED = "platforms_loaded"
DISCOVERY_DISPATCHED = "discovery_dispatched"


async def start_discovery(hass: HomeAssistant, hass_config, config_entry=None) -> bool:
    """Initialize of Node-RED Discovery."""

    async def async_device_message_received(msg, connection):
        """Process the received message."""
        component = msg[CONF_COMPONENT]
        server_id = msg[CONF_SERVER_ID]
        node_id = msg[CONF_NODE_ID]

        if component not in SUPPORTED_COMPONENTS:
            _LOGGER.warning(f"Integration {component} is not supported")
            return

        discovery_hash = f"{DOMAIN}-{server_id}-{node_id}"
        data = hass.data[DOMAIN_DATA]

        _LOGGER.debug(f"Discovery message: {msg}")

        if ALREADY_DISCOVERED not in data:
            data[ALREADY_DISCOVERED] = set()

        # Check if already discovered
        already_discovered = discovery_hash in data[ALREADY_DISCOVERED]

        if already_discovered:
            if CONF_REMOVE in msg:
                log_text = "Removing"
            else:
                log_text = "Updating"

            _LOGGER.info(f"{log_text} {component} {server_id} {node_id}")

            async_dispatcher_send(
                hass, NODERED_DISCOVERY_UPDATED.format(discovery_hash), msg, connection
            )
        else:
            # Add component - ensure platform is set up first
            _LOGGER.info(f"Creating {component} {server_id} {node_id}")

            async with data.setdefault(PLATFORM_SETUP_LOCK, {}).setdefault(
                component, asyncio.Lock()
            ):
                if component not in data.get(PLATFORMS_LOADED, set()):
                    await hass.config_entries.async_forward_entry_setups(
                        config_entry, [component]
                    )
                    data.setdefault(PLATFORMS_LOADED, set()).add(component)

            data[ALREADY_DISCOVERED].add(discovery_hash)

            async_dispatcher_send(
                hass, NODERED_DISCOVERY_NEW.format(component), msg, connection
            )

    hass.data[DOMAIN_DATA][DISCOVERY_DISPATCHED] = async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY,
        async_device_message_received,
    )


def stop_discovery(hass: HomeAssistant):
    """Remove discovery dispatcher."""
    hass.data[DOMAIN_DATA][DISCOVERY_DISPATCHED]()
