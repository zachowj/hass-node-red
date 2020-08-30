"""Support for Node-RED discovery."""
import asyncio
import logging

from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    CONF_BINARY_SENSOR,
    CONF_COMPONENT,
    CONF_NODE_ID,
    CONF_REMOVE,
    CONF_SENSOR,
    CONF_SERVER_ID,
    CONF_SWITCH,
    DOMAIN,
    DOMAIN_DATA,
    NODERED_DISCOVERY,
    NODERED_DISCOVERY_NEW,
    NODERED_DISCOVERY_UPDATED,
)

SUPPORTED_COMPONENTS = [
    CONF_SWITCH,
    CONF_BINARY_SENSOR,
    CONF_SENSOR,
]

_LOGGER = logging.getLogger(__name__)

ALREADY_DISCOVERED = "discovered_components"
CHANGE_ENTITY_TYPE = "change_entity_type"
CONFIG_ENTRY_LOCK = "config_entry_lock"
CONFIG_ENTRY_IS_SETUP = "config_entry_is_setup"
DISCOVERY_DISPATCHED = "discovery_dispatched"


async def start_discovery(
    hass: HomeAssistantType, hass_config, config_entry=None
) -> bool:
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
            data[ALREADY_DISCOVERED] = {}
        if discovery_hash in data[ALREADY_DISCOVERED]:

            if data[ALREADY_DISCOVERED][discovery_hash] != component:
                # Remove old
                log_text = f"Changing {data[ALREADY_DISCOVERED][discovery_hash]} to"
                msg[CONF_REMOVE] = CHANGE_ENTITY_TYPE
            elif CONF_REMOVE in msg:
                log_text = "Removing"
            else:
                # Dispatch update
                log_text = "Updating"

            _LOGGER.info(f"{log_text} {component} {server_id} {node_id}")

            data[ALREADY_DISCOVERED][discovery_hash] = component
            async_dispatcher_send(
                hass, NODERED_DISCOVERY_UPDATED.format(discovery_hash), msg, connection
            )
        else:
            # Add component
            _LOGGER.info(f"Creating {component} {server_id} {node_id}")
            data[ALREADY_DISCOVERED][discovery_hash] = component

            async with data[CONFIG_ENTRY_LOCK]:
                if component not in data[CONFIG_ENTRY_IS_SETUP]:
                    await hass.config_entries.async_forward_entry_setup(
                        config_entry, component
                    )
                    data[CONFIG_ENTRY_IS_SETUP].add(component)

            async_dispatcher_send(
                hass, NODERED_DISCOVERY_NEW.format(component), msg, connection
            )

    hass.data[DOMAIN_DATA][CONFIG_ENTRY_LOCK] = asyncio.Lock()
    hass.data[DOMAIN_DATA][CONFIG_ENTRY_IS_SETUP] = set()

    hass.data[DOMAIN_DATA][DISCOVERY_DISPATCHED] = async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY,
        async_device_message_received,
    )


def stop_discovery(hass: HomeAssistantType):
    """Remove discovery dispatcher."""
    hass.data[DOMAIN_DATA][DISCOVERY_DISPATCHED]()
