"""Tests for sentence websocket triggers and helpers."""

import asyncio
from collections.abc import Callable
import sys
import types
from typing import Any, cast

import pytest
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered import sentence as sentence_mod, websocket
from custom_components.nodered.sentence import convert_recognize_result_to_dict
from homeassistant.components.websocket_api.messages import error_message
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


def test_convert_recognize_result_to_dict_various(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """convert_recognize_result_to_dict should serialize different types."""

    # Sentence-like object
    class DummySentence:
        def __init__(self, text: str) -> None:
            self.text = text
            self.pattern = None

    monkeypatch.setattr(sentence_mod, "Sentence", DummySentence)

    s = DummySentence("hello")
    assert convert_recognize_result_to_dict(s) == {"text": "hello", "pattern": None}

    # Object with __dict__ and nested structures
    class Obj:
        def __init__(self) -> None:
            self.a = 1
            self.b = [2, "x"]
            self.c = {"k": 3}

    o = Obj()
    assert convert_recognize_result_to_dict(o) == {"a": 1, "b": [2, "x"], "c": {"k": 3}}

    # Lists and dicts
    assert convert_recognize_result_to_dict([1, 2, "x"]) == [1, 2, "x"]
    assert convert_recognize_result_to_dict({"k": "v"}) == {"k": "v"}

    # Primitive
    primitive_value = 5
    assert convert_recognize_result_to_dict(primitive_value) == primitive_value

    # Fallback for non-serializable (object with no __dict__)
    obj = object()
    assert isinstance(convert_recognize_result_to_dict(obj), str)


@pytest.mark.asyncio
async def test_websocket_sentence_manager_none_returns_value_error(
    hass: HomeAssistant,
    enable_custom_integrations: Any,
    hass_ws_client: WebSocketGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When get_agent_manager returns None, websocket_sentence should send value_error."""
    # Ensure custom integrations are enabled for this test
    _ = enable_custom_integrations

    # Simulate manager missing by creating fake conversation submodules
    agent_manager_mod = types.ModuleType(
        "homeassistant.components.conversation.agent_manager"
    )

    def get_agent_manager(_hass: Any) -> None:
        return None

    agent_manager_mod.get_agent_manager = get_agent_manager  # pyright: ignore[reportAttributeAccessIssue]

    trigger_mod = types.ModuleType("homeassistant.components.conversation.trigger")

    class TriggerDetails:
        def __init__(self, sentences: list[str], trigger: Any) -> None:
            self.sentences = sentences
            self.trigger = trigger

    trigger_mod.TriggerDetails = TriggerDetails  # pyright: ignore[reportAttributeAccessIssue]

    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.conversation.agent_manager",
        agent_manager_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.conversation.trigger",
        trigger_mod,
    )

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)

    msg = {
        "id": 10,
        "type": "nodered/sentence",
        "server_id": "s1",
        "sentences": ["hi"],
        "response": "Done",
        "response_timeout": 1,
        "response_type": "fixed",
    }

    await client.send_json(msg)
    resp = await client.receive_json()

    assert resp == error_message(
        msg["id"], "value_error", "Conversation integration not loaded"
    )


@pytest.mark.asyncio
async def test_websocket_sentence_dynamic_response_flow(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dynamic response flow: trigger emits event and response delivered."""
    # Fake manager that registers a trigger and returns a removal function
    captured: dict[str, Any] = {}

    class FakeManager:
        def register_trigger(self, details: Any) -> Callable[[], None]:
            # details.trigger includes the handler; preserve it
            captured["handler"] = details.trigger

            def remove() -> None:
                captured["removed"] = True

            return remove

    # Provide get_agent_manager via a fake conversation submodule
    agent_manager_mod = types.ModuleType(
        "homeassistant.components.conversation.agent_manager"
    )

    def get_agent_manager(_hass: Any) -> Any:
        return FakeManager()

    agent_manager_mod.get_agent_manager = get_agent_manager  # pyright: ignore[reportAttributeAccessIssue]

    trigger_mod = types.ModuleType("homeassistant.components.conversation.trigger")

    class TriggerDetails:
        def __init__(self, sentences: list[str], trigger: Any) -> None:
            self.sentences = sentences
            self.trigger = trigger

    trigger_mod.TriggerDetails = TriggerDetails  # pyright: ignore[reportAttributeAccessIssue]

    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.conversation.agent_manager",
        agent_manager_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.conversation.trigger",
        trigger_mod,
    )

    message_id = 123
    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)

    msg = {
        "id": message_id,
        "type": "nodered/sentence",
        "server_id": "s",
        "sentences": ["hello"],
        "response": "Done",
        "response_type": "dynamic",
        "response_timeout": 1,
    }

    # register the trigger via websocket
    await client.send_json(msg)
    await client.receive_json()  # result_message for registration

    # Confirm the manager captured the handler
    handler = captured["handler"]
    task = asyncio.create_task(handler("hello world", None, "dev1"))

    # Ensure the event was sent and received by the websocket client
    event = await client.receive_json()
    assert event["type"] == "event"
    assert event["id"] == message_id

    # Now send the response via websocket_sentence_response
    await client.send_json(
        {
            "id": 200,
            "type": "nodered/sentence_response",
            "response_id": message_id,
            "response": "the answer",
        }
    )
    await client.receive_json()  # result_message for response

    # Task should complete with the response
    result = await asyncio.wait_for(task, timeout=1)
    assert result == "the answer"


def test_websocket_sentence_response_not_found() -> None:
    """No matching response future: websocket_sentence_response should send error."""
    conn = FakeConnection()
    msg = {"id": 201, "response_id": 9999, "response": "x"}

    func: Any = sentence_mod.websocket_sentence_response
    while hasattr(func, "__wrapped__"):
        func = cast("Any", func.__wrapped__)  # type: ignore[attr-defined]
    # Call synchronously since function is async but quick

    asyncio.get_event_loop().run_until_complete(func(None, conn, msg))  # type: ignore[misc]

    assert conn.sent == error_message(
        msg["id"],
        "sentence_response_not_found",
        f"Sentence response not found for id: {msg['response_id']}",
    )
