"""Test nodered setup process."""

from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered.const import DOMAIN, DOMAIN_DATA


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
async def test_setup_unload_and_reload_entry(
    hass: HomeAssistant, enable_custom_integrations: Any
) -> None:
    """Test entry setup, reload, and unload using HA lifecycle."""
    _ = enable_custom_integrations
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)

    # Simulate Home Assistant setup lifecycle
    setup_result = await hass.config_entries.async_setup(config_entry.entry_id)
    if not setup_result:
        pytest.fail("Config entry setup failed.")

    if config_entry.state != ConfigEntryState.LOADED:
        pytest.fail(f"Config entry not loaded: {config_entry.state}")
    if DOMAIN_DATA not in hass.data:
        pytest.fail("Domain data missing after setup.")

    # Simulate reload
    result = await hass.config_entries.async_reload(config_entry.entry_id)
    if result is not True:
        pytest.fail(f"Reload entry did not return True: {result}")
    if config_entry.state != ConfigEntryState.LOADED:
        pytest.fail(f"Config entry not loaded after reload: {config_entry.state}")
    if DOMAIN_DATA not in hass.data:
        pytest.fail("Domain data missing after reload.")

    # Simulate unload
    result = await hass.config_entries.async_unload(config_entry.entry_id)
    if not result:
        pytest.fail("Failed to unload Node-RED entry.")
    if config_entry.state != ConfigEntryState.NOT_LOADED:
        pytest.fail(f"Config entry not unloaded: {config_entry.state}")
    if DOMAIN_DATA in hass.data:
        pytest.fail("Domain data still present after unload.")
