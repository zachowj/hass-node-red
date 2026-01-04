"""Test nodered config flow."""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered.const import DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture() -> Generator[None]:
    """Prevent setup."""
    with (
        patch(
            "custom_components.nodered.async_setup",
            return_value=True,
            create=True,
        ),
        patch(
            "custom_components.nodered.async_setup_entry",
            return_value=True,
            create=True,
        ),
    ):
        yield


# Here we simulate a successful config flow from the backend.
async def test_successful_config_flow(hass: HomeAssistant) -> None:
    """Test a successful config flow."""

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"

    # Test submitting the form
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Node-RED"
    assert result.get("data") == {}
    assert result.get("result")


async def test_already_configured(hass: HomeAssistant) -> None:
    """Test we handle already configured."""

    # Create a mock entry so we can check against it
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Node-RED",
        data={},
        unique_id="unique_test_id",
    )
    entry.add_to_hass(hass)

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows abort
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "single_instance_allowed"


async def test_abort_if_in_data(hass: HomeAssistant) -> None:
    """Test we abort if component is already loaded."""

    # Set the domain in hass.data
    hass.data[DOMAIN] = {"loaded": True}

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows abort
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "single_instance_allowed"
