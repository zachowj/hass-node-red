import asyncio
from enum import Enum
import logging
from typing import Any

from hassil.expression import Sentence
from hassil.recognize import RecognizeResult
from homeassistant.components.websocket_api import (
    async_response,
    error_message,
    event_message,
    require_admin,
    result_message,
    websocket_command,
)
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.const import CONF_ID, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import CONF_SERVER_ID

_LOGGER = logging.getLogger(__name__)

response_futures: dict[str, asyncio.Future] = {}
response_lock = asyncio.Lock()


class ResponseType(Enum):
    FIXED = "fixed"
    DYNAMIC = "dynamic"


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/sentence",
        vol.Required(CONF_SERVER_ID): cv.string,
        vol.Required("sentences", default=[]): [cv.string],
        vol.Optional("response", default="Done"): cv.string,
        vol.Optional("response_type", default=ResponseType.FIXED): vol.Coerce(
            ResponseType
        ),
        vol.Optional("response_timeout", default=1): cv.positive_float,
    }
)
@async_response
async def websocket_sentence(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create sentence trigger."""
    message_id = msg[CONF_ID]
    sentences = msg["sentences"]
    response = msg["response"]
    response_timeout = msg["response_timeout"]
    response_type = msg["response_type"]

    @callback
    async def handle_trigger(
        sentence: str,
        result: RecognizeResult | None = None,
        device_id: str | None = None,
    ) -> str:
        """
        Handle Sentence trigger.
        RecognizeResult was added in 2023.8.0
        device_id was added in 2024.4.0
        """

        # RecognizeResult in 2024.12 is not serializable, so we need to convert it to a serializable format
        serialized = convert_recognize_result_to_dict(result)

        _LOGGER.debug(f"Sentence trigger: {sentence}")
        connection.send_message(
            event_message(
                message_id,
                {
                    "data": {
                        "sentence": sentence,
                        "result": serialized,
                        "deviceId": device_id,
                        "responseId": message_id,
                    }
                },
            )
        )

        if response_type == ResponseType.DYNAMIC:
            async with response_lock:
                if message_id not in response_futures:
                    response_futures[message_id] = hass.loop.create_future()

            try:
                result = await asyncio.wait_for(
                    response_futures[message_id], response_timeout
                )
                _LOGGER.debug(
                    f"Sentence response {message_id} received with response: {result}"
                )
                return result
            except asyncio.TimeoutError:
                _LOGGER.debug(
                    f"Timeout reached for sentence response {message_id}. Continuing..."
                )
                # Remove the event from the dictionary after timeout
                del response_futures[message_id]

        return response

    def remove_trigger() -> None:
        """Remove sentence trigger."""

        async def _remove_future() -> None:
            async with response_lock:
                if message_id in response_futures:
                    del response_futures[message_id]

        hass.async_create_task(_remove_future())
        _remove_trigger()
        _LOGGER.info(f"Sentence trigger removed: {sentences}")

    try:
        from homeassistant.components.conversation import get_agent_manager
        from homeassistant.components.conversation.trigger import TriggerDetails

        manager = get_agent_manager(hass)
        if manager is None:
            raise ValueError("Conversation integration not loaded")

        _remove_trigger = manager.register_trigger(
            TriggerDetails(sentences, handle_trigger)
        )
    except ImportError:
        # Fallback for Home Assistant versions before 2025.10.0
        from homeassistant.components.conversation.default_agent import (
            DATA_DEFAULT_ENTITY,
            DefaultAgent,
        )

        default_agent = hass.data[DATA_DEFAULT_ENTITY]
        assert isinstance(default_agent, DefaultAgent)

        _remove_trigger = default_agent.register_trigger(sentences, handle_trigger)
    except ValueError as err:
        connection.send_message(error_message(message_id, "value_error", str(err)))
        return
    except Exception as err:
        connection.send_message(error_message(message_id, "unknown_error", str(err)))
        return

    if response_type == ResponseType.FIXED:
        _LOGGER.info(f"Sentence trigger created: {sentences}")
    else:
        _LOGGER.info(
            f"Sentence trigger created: {sentences} with dynamic response #{message_id} and timeout of {response_timeout} seconds"
        )
    connection.subscriptions[msg[CONF_ID]] = remove_trigger
    connection.send_message(result_message(message_id))


@require_admin
@websocket_command(
    {
        vol.Required(CONF_TYPE): "nodered/sentence_response",
        vol.Required("response_id"): cv.positive_int,
        vol.Required("response"): cv.string,
    }
)
@async_response
async def websocket_sentence_response(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send response to sentence trigger."""
    message_id = msg[CONF_ID]
    response_id = msg["response_id"]
    response = msg["response"]

    async with response_lock:
        # Print the current response_futures keys (ids)
        if response_id in response_futures:
            # Set the message as the result
            response_futures[response_id].set_result(response)
            # Remove the event from the dictionary after dispatching
            del response_futures[response_id]
            _LOGGER.info(f"Sentence response received: {response}")
            connection.send_message(result_message(message_id))
        else:
            message = f"Sentence response not found for id: {response_id}"
            _LOGGER.warning(message)
            connection.send_message(
                error_message(message_id, "sentence_response_not_found", message),
            )


def convert_recognize_result_to_dict(result: Any) -> dict:
    """
    Serializes a RecognizeResult object into a JSON-serializable dictionary.
    """

    def serialize(obj):
        if isinstance(obj, Sentence):
            # Custom serialization for Sentence
            return {
                "text": obj.text,
                "pattern": (
                    obj.pattern.pattern
                    if hasattr(obj, "pattern") and getattr(obj, "pattern") is not None
                    else None
                ),
            }
        elif hasattr(obj, "__dict__"):
            # For objects with attributes, serialize attributes
            return {key: serialize(value) for key, value in vars(obj).items()}
        elif isinstance(obj, list):
            # Recursively handle lists
            return [serialize(item) for item in obj]
        elif isinstance(obj, dict):
            # Recursively handle dictionaries
            return {key: serialize(value) for key, value in obj.items()}
        elif isinstance(obj, (int, float, str, type(None))):
            # Primitive types are already serializable
            return obj
        else:
            # Fallback for non-serializable types
            return str(obj)

    return serialize(result)
