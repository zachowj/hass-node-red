"""Component to integrate with node-red.

For more details about this component, please refer to
https://github.com/zachowj/hass-node-red
"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity_registry import async_entries_for_device, async_get

from .const import CONF_VERSION, DOMAIN, DOMAIN_DATA, STARTUP_MESSAGE, WEBHOOKS
from .discovery import (
    PLATFORMS_LOADED,
    SUPPORTED_COMPONENTS,
    start_discovery,
    stop_discovery,
)
from .version import __version__
from .websocket import register_websocket_handlers, unregister_all_webhooks

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    domain_data = hass.data.setdefault(DOMAIN_DATA, {})

    if not domain_data:
        _LOGGER.info(STARTUP_MESSAGE)

    # Initialize webhook tracking
    domain_data.setdefault(WEBHOOKS, set())

    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_COMPONENTS)
    domain_data[PLATFORMS_LOADED] = set(SUPPORTED_COMPONENTS)

    register_websocket_handlers(hass)
    await start_discovery(hass, domain_data)
    hass.bus.async_fire(DOMAIN, {CONF_TYPE: "loaded", CONF_VERSION: __version__})

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    # Unregister all webhooks before unloading platforms
    unregister_all_webhooks(hass)

    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in hass.data[DOMAIN_DATA].get(PLATFORMS_LOADED, set())
            ]
        )
    )

    if unloaded:
        stop_discovery(hass)
        hass.data.pop(DOMAIN_DATA)
        hass.bus.async_fire(DOMAIN, {CONF_TYPE: "unloaded"})

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, device_entry: DeviceEntry
) -> bool:
    """Remove a entry from the device registry."""
    entity_registry = async_get(hass)
    entries = async_entries_for_device(entity_registry, device_entry.id)
    # Remove entities from device before removing device
    # so the entities are not removed from HA
    if entries:
        for entry in entries:
            entity_registry.async_update_entity(entry.entity_id, device_id=None)

    return True
