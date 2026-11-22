"""Websocket integration tests for sensor/binary_sensor availability."""

from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered.const import CONF_CONTRIB_VERSION, DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State


async def _setup_nodered(hass: HomeAssistant) -> None:
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_sensor_discovery_without_state_legacy_is_unknown(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Without presence-available: discovery without state is Unknown."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "sensor",
            "server_id": "s1",
            "node_id": "no-state",
            "config": {"name": "No State Sensor"},
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.no_state_sensor")
    assert state is not None
    assert state.state == STATE_UNKNOWN


async def test_sensor_discovery_without_state_presence_is_unavailable(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """With presence-available: discovery without state is Unavailable."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.80.3"}
    )
    assert (await client.receive_json())["success"]

    await client.send_json(
        {
            "id": 2,
            "type": "nodered/discovery",
            "component": "sensor",
            "server_id": "s1",
            "node_id": "no-state",
            "config": {"name": "No State Sensor"},
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.no_state_sensor")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_sensor_discovery_with_state_then_entity_updates(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Resend-shaped discovery is available; entity updates flip availability."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "sensor",
            "server_id": "s1",
            "node_id": "with-state",
            "state": 21.5,
            "attributes": {"source": "resend"},
            "config": {"name": "Resend Sensor"},
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.resend_sensor")
    assert state is not None
    assert state.state == "21.5"
    assert state.attributes.get("source") == "resend"

    # Legacy entity update (state, no available) keeps/sets available
    await client.send_json(
        {
            "id": 2,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "with-state",
            "state": 22.0,
        }
    )
    resp2 = await client.receive_json()
    assert resp2["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.resend_sensor")
    assert state is not None
    assert state.state == "22.0"

    # Unavailable with new reading retained for later
    await client.send_json(
        {
            "id": 3,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "with-state",
            "state": 19.0,
            "attributes": {"source": "live"},
            "available": False,
        }
    )
    resp3 = await client.receive_json()
    assert resp3["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.resend_sensor")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Availability-only restore — value/attrs come back without resend
    await client.send_json(
        {
            "id": 4,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "with-state",
            "available": True,
        }
    )
    resp4 = await client.receive_json()
    assert resp4["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.resend_sensor")
    assert state is not None
    assert state.state == "19.0"
    assert state.attributes.get("source") == "live"


async def test_sensor_availability_only_does_not_wipe_attributes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Availability-only entity messages must not clear attributes."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "sensor",
            "server_id": "s1",
            "node_id": "attrs",
            "state": 1,
            "attributes": {"keep": True},
            "config": {"name": "Attrs Sensor"},
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    await client.send_json(
        {
            "id": 2,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "attrs",
            "available": False,
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    await client.send_json(
        {
            "id": 3,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "attrs",
            "available": True,
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get("sensor.attrs_sensor")
    assert state is not None
    assert state.state == "1"
    assert state.attributes.get("keep") is True


async def test_binary_sensor_discovery_without_state_legacy_is_unknown(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Without presence-available: binary discovery without state is Unknown."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "binary_sensor",
            "server_id": "s1",
            "node_id": "bs-no-state",
            "config": {"name": "No State Binary"},
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.no_state_binary")
    assert state is not None
    assert state.state == STATE_UNKNOWN


async def test_binary_sensor_discovery_without_state_presence_is_unavailable(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """With presence-available: binary discovery without state is Unavailable."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.80.3"}
    )
    assert (await client.receive_json())["success"]

    await client.send_json(
        {
            "id": 2,
            "type": "nodered/discovery",
            "component": "binary_sensor",
            "server_id": "s1",
            "node_id": "bs-no-state",
            "config": {"name": "No State Binary"},
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.no_state_binary")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def _announce(client: Any) -> None:
    await client.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.80.3"}
    )
    assert (await client.receive_json())["success"]


async def _send(hass: HomeAssistant, client: Any, msg: dict[str, Any]) -> None:
    await client.send_json(msg)
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()


async def _add_unavailable_sensor(
    hass: HomeAssistant, client: Any, node_id: str
) -> None:
    """Discover a sensor with attributes, then mark it unavailable."""
    await _send(
        hass,
        client,
        {
            "id": 10,
            "type": "nodered/discovery",
            "component": "sensor",
            "server_id": "s1",
            "node_id": node_id,
            "state": 1,
            "attributes": {"keep": True},
            "config": {"name": node_id},
        },
    )
    await _send(
        hass,
        client,
        {
            "id": 11,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": node_id,
            "available": False,
        },
    )


async def _send_state_only(
    hass: HomeAssistant, client: Any, node_id: str
) -> State | None:
    await _send(
        hass,
        client,
        {
            "id": 12,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": node_id,
            "state": 2,
        },
    )
    return hass.states.get(f"sensor.{node_id}")


async def _send_available(
    hass: HomeAssistant, client: Any, node_id: str
) -> State | None:
    await _send(
        hass,
        client,
        {
            "id": 13,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": node_id,
            "available": True,
        },
    )
    return hass.states.get(f"sensor.{node_id}")


async def test_state_only_update_follows_its_own_connection(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Another connection's announce doesn't change how an update is read."""
    await _setup_nodered(hass)
    new_contrib = await hass_ws_client(hass)
    old_contrib = await hass_ws_client(hass)
    await _announce(new_contrib)
    await _add_unavailable_sensor(hass, new_contrib, "new")
    await _add_unavailable_sensor(hass, old_contrib, "old")

    state = await _send_state_only(hass, new_contrib, "new")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    state = await _send_available(hass, new_contrib, "new")
    assert state is not None
    assert state.state == "2"
    assert state.attributes.get("keep") is True

    state = await _send_state_only(hass, old_contrib, "old")
    assert state is not None
    assert state.state == "2"
    assert "keep" not in state.attributes


async def test_closing_a_connection_keeps_other_announces(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Closing one connection doesn't clear another connection's announce."""
    await _setup_nodered(hass)
    closing = await hass_ws_client(hass)
    staying = await hass_ws_client(hass)
    await _announce(closing)
    await _announce(staying)
    await _add_unavailable_sensor(hass, staying, "staying")

    await closing.close()
    await hass.async_block_till_done()

    state = await _send_state_only(hass, staying, "staying")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    state = await _send_available(hass, staying, "staying")
    assert state is not None
    assert state.state == "2"
    assert state.attributes.get("keep") is True


async def test_reconnect_without_announce_is_legacy(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """A reconnect that doesn't announce gets legacy handling."""
    await _setup_nodered(hass)
    first = await hass_ws_client(hass)
    await _announce(first)
    await _add_unavailable_sensor(hass, first, "sensor")
    await first.close()
    await hass.async_block_till_done()

    reconnected = await hass_ws_client(hass)
    state = await _send_state_only(hass, reconnected, "sensor")
    assert state is not None
    assert state.state == "2"
    assert "keep" not in state.attributes
