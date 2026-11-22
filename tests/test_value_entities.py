"""Websocket tests shared by the number, text, select and time entities."""

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered.const import DOMAIN
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State

VALUE_ENTITIES = [
    pytest.param("number", {}, 5, "5", id="number"),
    pytest.param("text", {}, "hello", "hello", id="text"),
    pytest.param("select", {"options": ["a", "b"]}, "b", "b", id="select"),
    pytest.param("time", {}, "12:34:00", "12:34:00", id="time"),
]


async def _setup_nodered(hass: HomeAssistant) -> None:
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize(("component", "config", "value", "expected"), VALUE_ENTITIES)
@pytest.mark.parametrize(
    "update",
    [
        pytest.param({"available": False}, id="available"),
        pytest.param({"attributes": {"foo": "bar"}}, id="attributes"),
    ],
)
async def test_update_without_state_keeps_value(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    config: dict[str, Any],
    value: Any,
    expected: str,
    update: dict[str, Any],
) -> None:
    """An update without state leaves the value as it was."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)
    entity_id = f"{component}.value_entity"

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": component,
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Value Entity", **config},
            "state": value,
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    await client.send_json(
        {"id": 2, "type": "nodered/entity", "server_id": "s1", "node_id": "n1"} | update
    )
    assert (await client.receive_json())["success"]
    await client.send_json(
        {
            "id": 3,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "n1",
            "available": True,
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == expected


@pytest.mark.parametrize(
    ("component", "config"),
    [pytest.param(*p.values[:2], id=p.id) for p in VALUE_ENTITIES],
)
async def test_discovery_without_state_is_unknown(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    component: str,
    config: dict[str, Any],
) -> None:
    """Discovery without a state creates the entity with an unknown value."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": component,
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Value Entity", **config},
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get(f"{component}.value_entity")
    assert state is not None
    assert state.state == STATE_UNKNOWN


@pytest.mark.parametrize(("component", "config", "value", "expected"), VALUE_ENTITIES)
async def test_null_state_update_is_rejected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    config: dict[str, Any],
    value: Any,
    expected: str,
) -> None:
    """An update with a null state is rejected and the value is kept."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": component,
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Value Entity", **config},
            "state": value,
        }
    )
    assert (await client.receive_json())["success"]

    await client.send_json(
        {
            "id": 2,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "n1",
            "state": None,
        }
    )
    resp = await client.receive_json()
    assert not resp["success"]
    assert resp["error"]["code"] == "invalid_format"
    await hass.async_block_till_done()

    state = hass.states.get(f"{component}.value_entity")
    assert state is not None
    assert state.state == expected


@pytest.mark.parametrize(
    ("component", "config"),
    [pytest.param(*p.values[:2], id=p.id) for p in VALUE_ENTITIES],
)
async def test_null_state_discovery_is_rejected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    component: str,
    config: dict[str, Any],
) -> None:
    """Discovery with a null state is rejected and no entity is created."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": component,
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Value Entity", **config},
            "state": None,
        }
    )
    resp = await client.receive_json()
    assert not resp["success"]
    assert resp["error"]["code"] == "invalid_format"
    await hass.async_block_till_done()

    assert hass.states.get(f"{component}.value_entity") is None


RESTORED_ENTITIES = [
    pytest.param(
        "number",
        "7",
        {
            "native_value": 7,
            "native_min_value": 0,
            "native_max_value": 100,
            "native_step": 1,
            "native_unit_of_measurement": None,
        },
        id="number",
    ),
    pytest.param(
        "text",
        "restored",
        {"native_value": "restored", "native_min": 0, "native_max": 100},
        id="text",
    ),
]


@pytest.mark.parametrize(("component", "restored", "extra_data"), RESTORED_ENTITIES)
@pytest.mark.parametrize(
    ("discovery", "expected"),
    [
        pytest.param({"state": 5}, "5", id="discovery_state"),
        pytest.param({}, None, id="no_discovery_state"),
    ],
)
async def test_discovery_value_wins_over_restored_state(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    restored: str,
    extra_data: dict[str, Any],
    discovery: dict[str, Any],
    expected: str | None,
) -> None:
    """The value sent at discovery is used; otherwise the restored state is."""
    entity_id = f"{component}.value_entity"
    mock_restore_cache_with_extra_data(hass, [(State(entity_id, restored), extra_data)])
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": component,
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Value Entity"},
        }
        | discovery
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == (expected or restored)
