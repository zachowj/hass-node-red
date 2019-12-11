"""Adds config flow for Node-RED."""
import logging

from homeassistant import config_entries

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class NodeRedFlowHandler(config_entries.ConfigFlow):
    """Config flow for Node-RED."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a user initiated set up flow to create a webhook."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user")
        return self.async_create_entry(title="Node-RED", data={},)
