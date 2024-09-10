"""Test nodered config flow."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
import pytest

from custom_components.nodered.const import CONF_NAME, DOMAIN


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.nodered.async_setup",
        return_value=True,
    ), patch(
        "custom_components.nodered.async_setup_entry",
        return_value=True,
    ):
        yield


# Here we simiulate a successful config flow from the backend.
async def test_successful_config_flow(hass):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == CONF_NAME
    assert result["data"] == {}
    assert result["result"]
