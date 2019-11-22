"""Websocket API for Node-RED."""
import voluptuous as vol
import logging
import json
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from homeassistant.components.websocket_api import (
    async_register_command,
    websocket_command,
    async_response,
    require_admin,
    result_message,
    event_message,
)
from homeassistant.const import CONF_STATE

from homeassistant.helpers.typing import HomeAssistantType
from .const import (
    DOMAIN,
    VERSION,
    NODERED_DISCOVERY,
    NODERED_ENTITY,
    CONF_SERVER_ID,
    CONF_NODE_ID,
)

_LOGGER = logging.getLogger(__name__)


def register_websocket_handlers(hass: HomeAssistantType):
    """Register the websocket handlers."""

    async_register_command(hass, websocket_version)
    async_register_command(hass, websocket_webhook)
    async_register_command(hass, websocket_discovery)
    async_register_command(hass, websocket_entity)


@require_admin
@websocket_command(
    {
        vol.Required("type"): "nodered/discovery",
        vol.Required("component"): cv.string,
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Optional("config", default={}): dict,
        vol.Optional(CONF_STATE): vol.Any(bool, str, int, float),
        vol.Optional("attributes"): dict,
        vol.Optional("remove"): bool,
    }
)
def websocket_discovery(hass, connection, msg):
    """Sensor command."""
    msg["connection"] = connection

    async_dispatcher_send(hass, NODERED_DISCOVERY.format(msg["component"]), msg)
    connection.send_message(result_message(msg["id"], {"success": True}))


@require_admin
@websocket_command(
    {
        vol.Required("type"): "nodered/entity",
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Required(CONF_STATE): vol.Any(bool, str, int, float),
        vol.Optional("attributes", default={}): dict,
    }
)
def websocket_entity(hass, connection, msg):
    """Sensor command."""

    async_dispatcher_send(
        hass, NODERED_ENTITY.format(msg[CONF_SERVER_ID], msg[CONF_NODE_ID]), msg
    )
    connection.send_message(result_message(msg["id"], {"success": True}))


@require_admin
@websocket_command({vol.Required("type"): "nodered/version"})
def websocket_version(hass, connection, msg):
    """Version command."""

    connection.send_message(result_message(msg["id"], VERSION))


@require_admin
@async_response
@websocket_command(
    {
        vol.Required("type"): "nodered/webhook",
        vol.Required("webhook_id"): cv.string,
        vol.Required("name"): cv.string,
        vol.Required(CONF_SERVER_ID): cv.string,
    }
)
async def websocket_webhook(hass, connection, msg):
    """Create webhook command."""
    webhook_id = msg["webhook_id"]

    @callback
    async def handle_webhook(hass, id, request):
        """Handle webhook callback."""
        body = await request.text()
        try:
            data = json.loads(body) if body else {}
        except ValueError:
            data = body

        _LOGGER.debug(f"Webhook recieved {id[:15]}..: {data}")
        connection.send_message(event_message(msg["id"], {"data": data}))

    def remove_webhook() -> None:
        """Remove webhook command."""
        try:
            hass.components.webhook.async_unregister(webhook_id)

        except ValueError:
            pass

        _LOGGER.info(f"Webhook removed: {webhook_id[:15]}..")
        connection.send_message(result_message(msg["id"], {"success": True}))

    try:
        hass.components.webhook.async_register(
            DOMAIN, msg["name"], webhook_id, handle_webhook
        )
    except ValueError:
        connection.send_message(result_message(msg["id"], {"success": False}))
        return

    _LOGGER.info(f"Webhook created: {webhook_id[:15]}..")
    connection.subscriptions[msg["id"]] = remove_webhook
    connection.send_message(result_message(msg["id"], {"success": True}))
