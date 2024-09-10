"""Test nodered setup process."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.nodered.const import DOMAIN, DOMAIN_DATA


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.
async def test_setup_unload_and_reload_entry(hass):
    """Test entry setup and unload."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data={})

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be.
    assert await async_setup_entry(hass, config_entry)
    assert DOMAIN_DATA in hass.data

    # Reload the entry and assert that the data from above is still there
    assert await async_reload_entry(hass, config_entry) is None
    assert DOMAIN_DATA in hass.data

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert DOMAIN_DATA not in hass.data
