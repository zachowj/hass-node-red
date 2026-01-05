"""Tests for websocket handlers."""

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant_custom_component.typing import WebSocketGenerator
import voluptuous as vol

from custom_components.nodered import websocket
from custom_components.nodered.const import DOMAIN, VERSION
from homeassistant.components.device_automation.exceptions import DeviceNotFound
from homeassistant.components.websocket_api.messages import (
    error_message,
    result_message,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from tests.helpers import create_device_with_entity


@pytest.mark.asyncio
async def test_websocket_device_action_calls_platform_and_sends_result(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    called: dict[str, Any] = {}

    class Platform:
        async def async_call_action_from_config(
            self, _hass: Any, action: Any, _variables: Any, _context: Any
        ) -> None:
            called["action"] = action

    async def fake_get(_hass: Any, _domain: Any, _t: Any) -> Platform:
        return Platform()

    # Patch the object imported in the websocket module directly
    monkeypatch.setattr(
        websocket.device_automation, "async_get_device_automation_platform", fake_get
    )
    # Create a real entity registry entry so the handler can resolve it
    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create("sensor", "nodered", "foo", suggested_object_id="foo")

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {
        "id": 5,
        "action": {"domain": "light", "entity_id": "sensor.foo", "device_id": "dev-1"},
    }

    await client.send_json(
        {"id": msg["id"], "type": "nodered/device/action", "action": msg["action"]}
    )
    resp = await client.receive_json()

    # Platform should be called; at minimum we expect a success result message
    assert resp == result_message(msg["id"])


@pytest.mark.asyncio
async def test_websocket_device_action_entity_not_found(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    # entity lookup returns None (no entity created in registry)
    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {
        "id": 6,
        "action": {"domain": "light", "entity_id": "missing", "device_id": "dev-1"},
    }

    await client.send_json(
        {"id": msg["id"], "type": "nodered/device/action", "action": msg["action"]}
    )
    sent = await client.receive_json()
    # Should be an error message when entity not found
    assert sent == error_message(
        msg["id"], "entity_not_found", "Entity 'missing' not found"
    )


@pytest.mark.asyncio
async def test_websocket_device_action_handles_device_not_found(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    class Platform:
        async def async_call_action_from_config(
            self, _hass: Any, _action: Any, _variables: Any, _context: Any
        ) -> None:
            msg = "no device"
            raise DeviceNotFound(msg)

    async def fake_get2(_hass: Any, _domain: Any, _t: Any) -> Platform:
        return Platform()

    monkeypatch.setattr(
        websocket.device_automation, "async_get_device_automation_platform", fake_get2
    )
    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {
        "id": 7,
        "action": {"domain": "light", "device_id": "dev-2"},
    }

    await client.send_json(
        {"id": msg["id"], "type": "nodered/device/action", "action": msg["action"]}
    )
    sent = await client.receive_json()

    assert sent == error_message(msg["id"], "device_not_found", "no device")


@pytest.mark.asyncio
async def test_websocket_device_remove_handles_device_and_entities(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    # Use real device and entity registries
    # Create a config entry so we can link the device to it

    # Create a device and linked entity using the test helper
    _config_entry, _device, entity = create_device_with_entity(hass, "node-1")

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {"id": 8, "node_id": "node-1"}

    await client.send_json(
        {"id": msg["id"], "type": "nodered/device/remove", "node_id": msg["node_id"]}
    )
    resp = await client.receive_json()

    assert resp == result_message(msg["id"])
    # Device should be removed
    assert dr.async_get(hass).async_get_device({(DOMAIN, "node-1")}) is None
    # Entity should have device_id cleared
    updated_entry = er.async_get(hass).async_get(entity.entity_id)
    assert updated_entry is not None
    assert updated_entry.device_id is None


@pytest.mark.asyncio
async def test_websocket_discovery_and_entity_and_update_config_and_version(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    sent: list[tuple[str, dict[str, Any], Any | None]] = []
    # Monkeypatch the websocket module's dispatcher send to capture arguments
    monkeypatch.setattr(
        websocket,
        "async_dispatcher_send",
        lambda _hass2, sig, msg, conn=None: sent.append((sig, msg, conn)),
    )

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)

    msg = {"id": 9, "component": "sensor", "server_id": "s", "node_id": "n"}
    await client.send_json(
        {
            "id": msg["id"],
            "type": "nodered/discovery",
            "component": msg["component"],
            "server_id": msg["server_id"],
            "node_id": msg["node_id"],
        }
    )
    resp = await client.receive_json()
    assert resp == result_message(msg["id"])
    assert sent

    msg2 = {"id": 10, "server_id": "s", "node_id": "n", "state": True}
    await client.send_json(
        {
            "id": msg2["id"],
            "type": "nodered/entity",
            "server_id": "s",
            "node_id": "n",
            "state": True,
        }
    )
    resp2 = await client.receive_json()
    assert resp2 == result_message(msg2["id"])

    msg3 = {"id": 11, "server_id": "s", "node_id": "n", "config": {}}
    await client.send_json(
        {
            "id": msg3["id"],
            "type": "nodered/entity/update_config",
            "server_id": "s",
            "node_id": "n",
            "config": {},
        }
    )
    resp3 = await client.receive_json()
    assert resp3 == result_message(msg3["id"])

    # version
    await client.send_json({"id": 12, "type": "nodered/version"})
    resp4 = await client.receive_json()
    assert resp4 == result_message(12, VERSION)


@pytest.mark.asyncio
async def test_websocket_webhook_register_handle_and_remove(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Register a webhook and ensure requests forward to the websocket connection."""
    # Capture handler during registration instead of inspecting hass.data
    captured: dict[str, Any] = {}

    real_register = websocket.webhook_async_register

    def fake_register(
        _hass2: HomeAssistant,
        _domain: str,
        _name: str,
        _webhook_id: str,
        _handler: Any,
        allowed_methods: Any = None,
    ) -> None:
        captured["webhook_id"] = _webhook_id
        captured["handler"] = _handler
        captured["allowed_methods"] = allowed_methods
        # Call through to the real register so HA state is populated
        return real_register(
            _hass2,
            _domain,
            _name,
            _webhook_id,
            _handler,
            allowed_methods=allowed_methods,
        )

    # Patch the registration function to capture the handler BEFORE the webhook
    # registration message is sent so we capture the handler when HA registers it.
    monkeypatch.setattr(websocket, "webhook_async_register", fake_register)

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {
        "id": 13,
        "server_id": "s1",
        "name": "n",
        "webhook_id": "wid",
    }

    await client.send_json(
        {
            "id": msg["id"],
            "type": "nodered/webhook",
            "server_id": msg["server_id"],
            "name": msg["name"],
            "webhook_id": msg["webhook_id"],
        }
    )
    resp = await client.receive_json()

    assert resp == result_message(msg["id"])

    assert captured.get("handler") is not None

    request = AsyncMock()
    request.text.return_value = json.dumps({"a": 1})
    request.headers = {"h": "v"}
    request.query = {"p": "v"}
    await captured["handler"](hass, captured["webhook_id"], request)

    # Ensure the websocket connection received the event message with the payload
    event = await client.receive_json()
    assert event["type"] == "event"
    assert event["event"]["data"]["payload"] == {"a": 1}
    assert event["event"]["data"]["headers"] == {"h": "v"}
    assert event["event"]["data"]["params"] == {"p": "v"}

    # Remove the webhook and verify it is removed from hass.data
    websocket.webhook_async_unregister(hass, msg["webhook_id"])

    # Handler should no longer be registered
    found = any(
        isinstance(val, dict) and msg["webhook_id"] in val for val in hass.data.values()
    )
    assert not found


@pytest.mark.asyncio
async def test_websocket_webhook_register_value_error(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Simulate registration failure when webhook async register raises ValueError."""

    def fake_register(
        _hass2: Any,
        _domain: str,
        _name: str,
        _webhook_id: str,
        _handler: Any,
        allowed_methods: Any = None,
    ) -> None:
        msg = "bad"
        raise ValueError(msg)

    monkeypatch.setattr(websocket, "webhook_async_register", fake_register)

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {"id": 14, "server_id": "s1", "name": "n", "webhook_id": "wid"}

    await client.send_json(
        {
            "id": msg["id"],
            "type": "nodered/webhook",
            "server_id": msg["server_id"],
            "name": msg["name"],
            "webhook_id": msg["webhook_id"],
        }
    )
    resp = await client.receive_json()

    assert resp == error_message(msg["id"], "value_error", "bad")


@pytest.mark.asyncio
async def test_websocket_device_trigger_success_and_errors(
    monkeypatch: pytest.MonkeyPatch,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    # Success path
    async def fake_validate(_hass2: Any, config: Any) -> list[Any]:
        return [config]

    async def fake_initialize(
        _hass2: Any,
        _cfg: Any,
        _forward: Any,
        _domain: str,
        _platform: str,
        _logger: Any,
    ) -> Any:
        # return a removecallback
        def remove() -> None:
            pass

        return remove

    monkeypatch.setattr(
        websocket.trigger, "async_validate_trigger_config", fake_validate
    )
    monkeypatch.setattr(websocket.trigger, "async_initialize_triggers", fake_initialize)

    websocket.register_websocket_handlers(hass)
    client = await hass_ws_client(hass)
    msg = {"id": 15, "node_id": "n1", "device_trigger": {}}

    await client.send_json(
        {
            "id": msg["id"],
            "type": "nodered/device/trigger",
            "node_id": msg["node_id"],
            "device_trigger": msg["device_trigger"],
        }
    )
    resp = await client.receive_json()
    assert resp == result_message(msg["id"])

    # Validation error: MultipleInvalid
    async def fake_validate_raise(_hass2: Any, _config: Any) -> list[Any]:
        raise vol.MultipleInvalid([vol.Invalid("x")])

    monkeypatch.setattr(
        websocket.trigger, "async_validate_trigger_config", fake_validate_raise
    )
    msg2 = {"id": 16, "node_id": "n2", "device_trigger": {}}
    await client.send_json(
        {
            "id": msg2["id"],
            "type": "nodered/device/trigger",
            "node_id": msg2["node_id"],
            "device_trigger": msg2["device_trigger"],
        }
    )
    resp2 = await client.receive_json()
    # Should have sent an error response
    assert resp2["success"] is False
    assert resp2["error"]["code"] == "invalid_trigger"

    # RuntimeError path
    async def fake_validate_ok(_hass2: Any, config: Any) -> list[Any]:
        return [config]

    async def fake_initialize_raise(
        _hass2: Any,
        _cfg: Any,
        _forward: Any,
        _domain: str,
        _platform: str,
        _logger: Any,
    ) -> Any:
        msg = "fail"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        websocket.trigger, "async_validate_trigger_config", fake_validate_ok
    )
    monkeypatch.setattr(
        websocket.trigger, "async_initialize_triggers", fake_initialize_raise
    )

    msg3 = {"id": 17, "node_id": "n3", "device_trigger": {}}
    await client.send_json(
        {
            "id": msg3["id"],
            "type": "nodered/device/trigger",
            "node_id": msg3["node_id"],
            "device_trigger": msg3["device_trigger"],
        }
    )
    resp3 = await client.receive_json()
    assert resp3["success"] is False
    assert resp3["error"]["code"] == "runtime_error"
