"""Websocket API for Node-RED."""
import json
import logging
from typing import Any

from hassil.recognize import RecognizeResult
from homeassistant.components import device_automation
from homeassistant.components.conversation import (
    HOME_ASSISTANT_AGENT,
    _get_agent_manager,
)
from homeassistant.components.conversation.default_agent import DefaultAgent
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.device_automation.exceptions import (
    DeviceNotFound,
    InvalidDeviceAutomationConfig,
)
from homeassistant.components.device_automation.trigger import TRIGGER_SCHEMA
from homeassistant.components.webhook import SUPPORTED_METHODS
from homeassistant.components.websocket_api import (
    async_register_command,
    async_response,
    error_message,
    event_message,
    require_admin,
    result_message,
    websocket_command,
)
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.const import (
    CONF_DOMAIN,
    CONF_ID,
    CONF_NAME,
    CONF_STATE,
    CONF_TYPE,
    CONF_WEBHOOK_ID,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    trigger,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_entries_for_device, async_get
from homeassistant.helpers.typing import HomeAssistantType
import voluptuous as vol

from .const import (
    CONF_ATTRIBUTES,
    CONF_COMPONENT,
    CONF_CONFIG,
    CONF_DEVICE_INFO,
    CONF_DEVICE_TRIGGER,
    CONF_NODE_ID,
    CONF_REMOVE,
    CONF_SERVER_ID,
    CONF_SUB_TYPE,
    DOMAIN,
    NODERED_CONFIG_UPDATE,
    NODERED_DISCOVERY,
    NODERED_ENTITY,
    VERSION,
)
from .utils import NodeRedJSONEncoder

CONF_ALLOWED_METHODS = "allowed_methods"
CONF_LOCAL_ONLY = "local_only"

_LOGGER = logging.getLogger(__name__)


def register_websocket_handlers(hass: HomeAssistantType):
    """Register the websocket handlers."""

    async_register_command(hass, websocket_device_action)
    async_register_command(hass, websocket_device_remove)
    async_register_command(hass, websocket_device_trigger)
    async_register_command(hass, websocket_discovery)
    async_register_command(hass, websocket_entity)
    async_register_command(hass, websocket_config_update)
    async_register_command(hass, websocket_version)
    async_register_command(hass, websocket_webhook)
    async_register_command(hass, websocket_sentence)


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/device/action",
        vol.Required("action"): cv.DEVICE_ACTION_SCHEMA,
    }
)
@async_response
async def websocket_device_action(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Sensor command."""
    context = connection.context(msg)
    platform = await device_automation.async_get_device_automation_platform(
        hass, msg["action"][CONF_DOMAIN], DeviceAutomationType.ACTION
    )

    try:
        await platform.async_call_action_from_config(hass, msg["action"], {}, context)
        connection.send_message(result_message(msg[CONF_ID]))
    except InvalidDeviceAutomationConfig as err:
        connection.send_message(error_message(msg[CONF_ID], "invalid_config", str(err)))
    except DeviceNotFound as err:
        connection.send_message(
            error_message(msg[CONF_ID], "device_not_found", str(err))
        )
    except Exception as err:
        connection.send_message(error_message(msg[CONF_ID], "unknown_error", str(err)))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/device/remove",
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Optional(CONF_CONFIG, default={}): dict,
    }
)
@async_response
async def websocket_device_remove(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Remove a device."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device({(DOMAIN, msg[CONF_NODE_ID])})
    if device is not None:
        entity_registry = async_get(hass)
        entries = async_entries_for_device(entity_registry, device.id)
        # Remove entities from device before removing device so the entities are not removed from HA
        if entries:
            for entry in entries:
                entity_registry.async_update_entity(entry.entity_id, device_id=None)

        device_registry.async_remove_device(device.id)

    connection.send_message(result_message(msg[CONF_ID]))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/discovery",
        vol.Required(CONF_COMPONENT): cv.string,
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Optional(CONF_CONFIG, default={}): dict,
        vol.Optional(CONF_STATE): vol.Any(bool, str, int, float, None),
        vol.Optional(CONF_ATTRIBUTES): dict,
        vol.Optional(CONF_REMOVE): bool,
        vol.Optional(CONF_DEVICE_INFO): dict,
        vol.Optional(CONF_DEVICE_TRIGGER): TRIGGER_SCHEMA,
        vol.Optional(CONF_SUB_TYPE): str,
    }
)
def websocket_discovery(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Sensor command."""
    async_dispatcher_send(
        hass, NODERED_DISCOVERY.format(msg[CONF_COMPONENT]), msg, connection
    )
    connection.send_message(result_message(msg[CONF_ID]))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/entity",
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Required(CONF_STATE): vol.Any(bool, str, int, float, None),
        vol.Optional(CONF_ATTRIBUTES, default={}): dict,
    }
)
def websocket_entity(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Sensor command."""

    async_dispatcher_send(
        hass, NODERED_ENTITY.format(msg[CONF_SERVER_ID], msg[CONF_NODE_ID]), msg
    )
    connection.send_message(result_message(msg[CONF_ID]))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/entity/update_config",
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Optional(CONF_CONFIG, default={}): dict,
    }
)
def websocket_config_update(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Sensor command."""

    async_dispatcher_send(
        hass, NODERED_CONFIG_UPDATE.format(msg[CONF_SERVER_ID], msg[CONF_NODE_ID]), msg
    )
    connection.send_message(result_message(msg[CONF_ID]))


@require_admin
@websocket_command({vol.Required(CONF_TYPE): "nodered/version"})
def websocket_version(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Version command."""

    connection.send_message(result_message(msg[CONF_ID], VERSION))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/webhook",
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_WEBHOOK_ID): cv.string,
        vol.Optional(CONF_ALLOWED_METHODS): vol.All(
            cv.ensure_list,
            [vol.All(vol.Upper, vol.In(SUPPORTED_METHODS))],
            vol.Unique(),
        ),
    }
)
@async_response
async def websocket_webhook(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create webhook command."""
    webhook_id = msg[CONF_WEBHOOK_ID]
    allowed_methods = msg.get(CONF_ALLOWED_METHODS)

    @callback
    async def handle_webhook(hass, id, request):
        """Handle webhook callback."""
        body = await request.text()
        try:
            payload = json.loads(body) if body else {}
        except ValueError:
            payload = body

        data = {
            "payload": payload,
            "headers": dict(request.headers),
            "params": dict(request.query),
        }

        _LOGGER.debug(f"Webhook received {id[:15]}..: {data}")
        connection.send_message(event_message(msg[CONF_ID], {"data": data}))

    def remove_webhook() -> None:
        """Remove webhook command."""
        try:
            hass.components.webhook.async_unregister(webhook_id)

        except ValueError:
            pass

        _LOGGER.info(f"Webhook removed: {webhook_id[:15]}..")
        connection.send_message(result_message(msg[CONF_ID]))

    try:
        hass.components.webhook.async_register(
            DOMAIN,
            msg[CONF_NAME],
            webhook_id,
            handle_webhook,
            allowed_methods=allowed_methods,
        )
    except ValueError as err:
        connection.send_message(error_message(msg[CONF_ID], "value_error", str(err)))
        return
    except Exception as err:
        connection.send_message(error_message(msg[CONF_ID], "unknown_error", str(err)))
        return

    _LOGGER.info(f"Webhook created: {webhook_id[:15]}..")
    connection.subscriptions[msg[CONF_ID]] = remove_webhook
    connection.send_message(result_message(msg[CONF_ID]))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/sentence",
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required("sentences", default=[]): [cv.string],
        vol.Optional("response", default="Done"): cv.string,
    }
)
@async_response
async def websocket_sentence(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create sentence trigger."""
    sentences = msg["sentences"]
    response = msg["response"]

    @callback
    async def handle_trigger(sentence: str, result: RecognizeResult = None) -> str:
        """Handle Sentence trigger."""
        """RecognizeResult was added in 2023.8.0"""

        _LOGGER.debug(f"Sentence trigger: {sentence}")
        connection.send_message(
            event_message(
                msg[CONF_ID], {"data": {"sentence": sentence, "result": result}}
            )
        )

        return response

    def remove_trigger() -> None:
        """Remove sentence trigger."""
        _remove_trigger()
        _LOGGER.info(f"Sentence trigger removed: {sentences}")

    try:
        default_agent = await _get_agent_manager(hass).async_get_agent(
            HOME_ASSISTANT_AGENT
        )
        assert isinstance(default_agent, DefaultAgent)

        _remove_trigger = default_agent.register_trigger(sentences, handle_trigger)
    except ValueError as err:
        connection.send_message(error_message(msg[CONF_ID], "value_error", str(err)))
        return
    except Exception as err:
        connection.send_message(error_message(msg[CONF_ID], "unknown_error", str(err)))
        return

    _LOGGER.info(f"Sentence trigger created: {sentences}")
    connection.subscriptions[msg[CONF_ID]] = remove_trigger
    connection.send_message(result_message(msg[CONF_ID]))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/device/trigger",
        vol.Required(CONF_NODE_ID): cv.string,
        vol.Required(CONF_DEVICE_TRIGGER, default={}): dict,
    }
)
@async_response
async def websocket_device_trigger(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create device trigger."""
    node_id = msg[CONF_NODE_ID]
    trigger_data = msg[CONF_DEVICE_TRIGGER]

    def forward_trigger(event, context=None):
        """Forward events to websocket."""
        message = event_message(
            msg[CONF_ID],
            {"type": "device_trigger", "data": event["trigger"]},
        )
        connection.send_message(
            json.dumps(message, cls=NodeRedJSONEncoder, allow_nan=False)
        )

    def unsubscribe() -> None:
        """Remove device trigger."""
        remove_trigger()
        _LOGGER.info(f"Device trigger removed: {node_id}")

    try:
        trigger_config = await trigger.async_validate_trigger_config(
            hass, [trigger_data]
        )
        remove_trigger = await trigger.async_initialize_triggers(
            hass,
            trigger_config,
            forward_trigger,
            DOMAIN,
            DOMAIN,
            _LOGGER.log,
        )

    except vol.MultipleInvalid as err:
        _LOGGER.error(
            f"Error initializing device trigger '{node_id}': {str(err)}",
        )
        connection.send_message(
            error_message(msg[CONF_ID], "invalid_trigger", str(err))
        )
        return
    except Exception as err:
        _LOGGER.error(
            f"Error initializing device trigger '{node_id}': {str(err)}",
        )
        connection.send_message(error_message(msg[CONF_ID], "unknown_error", str(err)))
        return

    _LOGGER.info(f"Device trigger created: {node_id}")
    _LOGGER.debug(f"Device trigger config for {node_id}: {trigger_data}")
    connection.subscriptions[msg[CONF_ID]] = unsubscribe
    connection.send_message(result_message(msg[CONF_ID]))
