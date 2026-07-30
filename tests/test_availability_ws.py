"""Websocket integration tests for sensor/binary_sensor availability."""

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered.const import CONF_CONTRIB_VERSION, DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant


async def _setup_nodered(
    hass: HomeAssistant, *, contrib_version: str | None = None
) -> None:
    data = {CONF_CONTRIB_VERSION: contrib_version} if contrib_version else {}
    config_entry = MockConfigEntry(domain=DOMAIN, data=data)
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
    await _setup_nodered(hass, contrib_version="0.80.3")
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
    await _setup_nodered(hass, contrib_version="0.80.3")
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
    assert state.state == STATE_UNAVAILABLE
