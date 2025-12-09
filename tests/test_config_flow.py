"""Test nodered config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.nodered.const import DOMAIN


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
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
async def test_successful_config_flow(hass, enable_custom_integrations):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test submitting the form
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Node-RED"
    assert result["data"] == {}
    assert result["result"]


# async def test_already_configured(hass, enable_custom_integrations):
#     """Test we handle already configured."""
#     # Create a mock entry so we can check against it
#     entry = config_entries.ConfigEntry(
#         version=1,
#         domain=DOMAIN,
#         title=CONF_NAME,
#         data={},
#         source="test",
#         entry_id="test",
#         unique_id="unique_test_id",
#         options={},
#     )

#     hass.config_entries.async_entries = (
#         lambda domain, include_ignore=None: [entry] if domain == DOMAIN else []
#     )

#     # Initialize a config flow
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )

#     # Check that the config flow shows abort
#     assert result["type"] == FlowResultType.ABORT
#     assert result["reason"] == "single_instance_allowed"


async def test_abort_if_in_data(hass, enable_custom_integrations):
    """Test we abort if component is already loaded."""
    # Set the domain in hass.data
    hass.data[DOMAIN] = {"loaded": True}

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows abort
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
