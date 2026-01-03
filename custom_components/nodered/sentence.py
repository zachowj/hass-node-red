"""Sentence platform for nodered."""

import asyncio
from enum import Enum
import logging
from typing import Any

from hassil.expression import Sentence
from hassil.recognize import RecognizeResult
import voluptuous as vol

from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.decorators import (
    async_response,
    require_admin,
    websocket_command,
)
from homeassistant.components.websocket_api.messages import (
    error_message,
    event_message,
    result_message,
)
from homeassistant.const import CONF_ID, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import CONF_SERVER_ID

_LOGGER = logging.getLogger(__name__)

response_futures: dict[str, asyncio.Future] = {}
response_lock = asyncio.Lock()


class ResponseType(Enum):
    """Enumeration for sentence response types used in Node-RED triggers."""

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
    ) -> Any:
        """Handle Sentence trigger.

        RecognizeResult was added in 2023.8.0
        device_id was added in 2024.4.0.
        """
        # RecognizeResult in 2024.12 is not serializable,
        # so we need to convert it to a serializable format
        serialized = convert_recognize_result_to_dict(result)

        _LOGGER.debug("Sentence trigger: %s", sentence)
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
                    "Sentence response %s received with response: %s",
                    message_id,
                    result,
                )
            except TimeoutError:
                _LOGGER.debug(
                    "Timeout reached for sentence response %s. Continuing...",
                    message_id,
                )
                # Remove the event from the dictionary after timeout
                del response_futures[message_id]
            else:
                return result

        return response

    def remove_trigger() -> None:
        """Remove sentence trigger."""

        async def _remove_future() -> None:
            async with response_lock:
                response_futures.pop(message_id, None)

        hass.async_create_task(_remove_future())
        _remove_trigger()
        _LOGGER.info("Sentence trigger removed: %s", sentences)

    try:
        from homeassistant.components.conversation.agent_manager import (  # noqa: PLC0415
            get_agent_manager,
        )
        from homeassistant.components.conversation.trigger import (  # noqa: PLC0415
            TriggerDetails,
        )

        manager = get_agent_manager(hass)
        if manager is None:
            raise ValueError("Conversation integration not loaded")  # noqa: TRY301

        _remove_trigger = manager.register_trigger(
            TriggerDetails(sentences, handle_trigger)  # type: ignore[arg-type]
        )
    except ImportError:
        # Fallback for Home Assistant versions before 2025.10.0
        from homeassistant.components.conversation.default_agent import (  # noqa: PLC0415
            DATA_DEFAULT_ENTITY,  # type: ignore[import]
            DefaultAgent,
        )

        default_agent = hass.data[DATA_DEFAULT_ENTITY]
        if not isinstance(default_agent, DefaultAgent):
            raise TypeError("default_agent is not an instance of DefaultAgent")  # noqa: B904

        _remove_trigger = default_agent.register_trigger(sentences, handle_trigger)  # type: ignore[arg-type]
    except ValueError as err:
        connection.send_message(error_message(message_id, "value_error", str(err)))
        return
    except TypeError as err:
        connection.send_message(error_message(message_id, "type_error", str(err)))
        return
    except RuntimeError as err:
        connection.send_message(error_message(message_id, "runtime_error", str(err)))
        return

    if response_type == ResponseType.FIXED:
        _LOGGER.info("Sentence trigger created: %s", sentences)
    else:
        _LOGGER.info(
            "Sentence trigger created: %s with dynamic response #%s and "
            "timeout of %s seconds",
            sentences,
            message_id,
            response_timeout,
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
            _LOGGER.info("Sentence response received: %s", response)
            connection.send_message(result_message(message_id))
        else:
            message = f"Sentence response not found for id: {response_id}"
            _LOGGER.warning(message)
            connection.send_message(
                error_message(message_id, "sentence_response_not_found", message),
            )


def convert_recognize_result_to_dict(result: Any) -> dict:
    """Serialize a RecognizeResult object into a JSON-serializable dictionary."""

    def serialize(obj: Any) -> Any:
        if isinstance(obj, Sentence):
            # Custom serialization for Sentence
            return {
                "text": obj.text,
                "pattern": (
                    obj.pattern.pattern
                    if hasattr(obj, "pattern") and obj.pattern is not None
                    else None
                ),
            }
        if hasattr(obj, "__dict__"):
            # For objects with attributes, serialize attributes
            return {key: serialize(value) for key, value in vars(obj).items()}
        if isinstance(obj, list):
            # Recursively handle lists
            return [serialize(item) for item in obj]
        if isinstance(obj, dict):
            # Recursively handle dictionaries
            return {key: serialize(value) for key, value in obj.items()}
        if isinstance(obj, (int, float, str, type(None))):
            # Primitive types are already serializable
            return obj
        # Fallback for non-serializable types
        return str(obj)

    return serialize(result)
