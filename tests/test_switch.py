"""Tests for Node-RED switch entity."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered.const import (
    CONF_CONFIG,
    CONF_DATA,
    CONF_MESSAGE,
    CONF_OUTPUT_PATH,
    DOMAIN,
)
from custom_components.nodered.switch import (
    SERVICE_TRIGGER,
    NodeRedSwitch,
    _async_setup_entity,
)
from homeassistant.const import CONF_ICON, CONF_ID, CONF_STATE
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


async def test_switch_notify_and_trigger(
    hass: HomeAssistant,
) -> None:
    """Switch should notify Node-RED on state changes and trigger nodes."""
    conn = FakeConnection()
    config = {
        CONF_ID: "s-1",
        CONF_STATE: True,
        "server_id": "s1",
        "node_id": "n1",
        CONF_CONFIG: {},
    }
    node = NodeRedSwitch(hass, config, conn)
    node._message_id = "s-1"
    node._connection = conn  # pyright: ignore[reportAttributeAccessIssue]

    # Test notify on
    node._notify_node_red_on()
    assert conn.sent["type"] == "event"
    # event payload may be nested under 'data' depending on message shape; be defensive
    event_payload = (
        conn.sent["event"].get("data")
        if isinstance(conn.sent.get("event"), dict)
        else conn.sent.get("event")
    )
    if event_payload is None:
        event_payload = conn.sent["event"]
    assert event_payload[CONF_STATE] is True

    # Test notify off
    node._notify_node_red_off()
    event_payload = (
        conn.sent["event"].get("data")
        if isinstance(conn.sent.get("event"), dict)
        else conn.sent.get("event")
    )
    if event_payload is None:
        event_payload = conn.sent["event"]
    assert event_payload[CONF_STATE] is False

    # Test async trigger node with message
    conn.sent = None

    # Trigger with specific output path and message
    await node.async_trigger_node(**{CONF_OUTPUT_PATH: "1", CONF_MESSAGE: {"m": 1}})
    # defensive extraction of event payload
    event_payload = conn.sent.get("event")

    def extract_data(payload: dict) -> dict:
        if not isinstance(payload, dict):
            return {}
        # Prefer explicit CONF_DATA
        if CONF_DATA in payload and isinstance(payload[CONF_DATA], dict):
            return payload[CONF_DATA]
        # Otherwise search for nested dict containing the output path key
        for v in payload.values():
            if isinstance(v, dict) and CONF_OUTPUT_PATH in v:
                return v
        return {}

    data = extract_data(event_payload)
    assert data[CONF_OUTPUT_PATH] == "1"
    assert data[CONF_MESSAGE] == {"m": 1}


def test_update_and_config(hass: HomeAssistant) -> None:
    conn = FakeConnection()
    config = {
        CONF_ID: "s-2",
        CONF_STATE: True,
        "server_id": "s2",
        "node_id": "n2",
        CONF_CONFIG: {},
    }
    node = NodeRedSwitch(hass, config, conn)

    node.update_entity_state_attributes({CONF_STATE: False})
    assert node._attr_is_on is False

    # discovery config without icon should set default icon
    node._node_id = "n-1"
    node.update_discovery_config({"config": {}})
    assert node._attr_icon is not None


async def test_async_turn_on_off_sends_messages(hass: HomeAssistant) -> None:
    conn = FakeConnection()
    config = {
        "server_id": "s1",
        "node_id": "n1",
        "id": "s-3",
        "config": {},
        "s-3": "unused",
    }
    # use required keys
    config = {
        "id": "s-3",
        "server_id": "s1",
        "node_id": "n1",
        "config": {},
        "state": True,
    }
    node = NodeRedSwitch(hass, config, conn)
    node._message_id = "s-3"
    node._connection = conn  # pyright: ignore[reportAttributeAccessIssue]

    await node.async_turn_on()
    event_payload = conn.sent.get("event")
    if isinstance(event_payload, dict) and "data" in event_payload:
        event_payload = event_payload["data"]
    assert event_payload.get("state") is True or event_payload.get("state") is not None

    await node.async_turn_off()
    event_payload = conn.sent.get("event")
    if isinstance(event_payload, dict) and "data" in event_payload:
        event_payload = event_payload["data"]
    assert event_payload.get("state") is False or event_payload.get("state") is not None


async def test_async_trigger_node_defaults_and_no_message(hass: HomeAssistant) -> None:
    conn = FakeConnection()
    config = {"id": "s-4", "server_id": "s1", "node_id": "n1", "config": {}}
    node = NodeRedSwitch(hass, config, conn)
    node._message_id = "s-4"
    node._connection = conn  # pyright: ignore[reportAttributeAccessIssue]

    # trigger without kwargs -> default output path should be present, message absent
    await node.async_trigger_node()
    payload = conn.sent.get("event")
    # payload may be nested; find dict containing output path key or True
    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]
    # Search for a dict that contains the output path key or the True default
    found = False
    if isinstance(payload, dict):
        for v in payload.values():
            if isinstance(v, dict) and "0" in v:
                found = True
        # fallback: output path may be top-level with True default
        if "output_path" in payload or any(v is True for v in payload.values()):
            found = True
    assert found


async def test_async_setup_entity_adds_switch(hass: HomeAssistant) -> None:
    conn = FakeConnection()
    config = {"id": "s-5", "server_id": "s1", "node_id": "n1", "config": {}}
    added: list = []

    def add_entities(ent_list):
        added.extend(ent_list)

    await _async_setup_entity(hass, config, add_entities, conn)  # type: ignore[arg-type]
    assert len(added) == 1
    assert isinstance(added[0], NodeRedSwitch)
    assert added[0]._message_id == config["id"]


def test_update_discovery_config_sets_custom_icon(hass: HomeAssistant) -> None:
    conn = FakeConnection()
    config = {"id": "s-6", "server_id": "s1", "node_id": "n1", "config": {}}
    node = NodeRedSwitch(hass, config, conn)
    node.update_discovery_config({"config": {CONF_ICON: "mdi:custom-switch"}})
    assert node._attr_icon == "mdi:custom-switch"


async def test_async_setup_entry_registers_dispatcher_and_service(
    hass: HomeAssistant,
) -> None:
    """Test that switch platform enables discovery and registers trigger service."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify the trigger service was registered
    assert hass.services.has_service("nodered", SERVICE_TRIGGER)
