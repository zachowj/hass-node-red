"""Websocket tests shared by the number, text, select and time entities."""

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered.const import DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
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
    ("component", "config", "expected"),
    [
        pytest.param("number", {}, "0.0", id="number"),
        pytest.param("number", {"min_value": 10}, "10", id="number_min"),
        pytest.param("text", {}, "", id="text"),
        pytest.param("text", {"min_length": 2}, STATE_UNKNOWN, id="text_min_length"),
        pytest.param("text", {"pattern": "[a-z]+"}, STATE_UNKNOWN, id="text_pattern"),
        pytest.param("select", {"options": ["a", "b"]}, "a", id="select"),
        pytest.param("time", {}, "00:00:00", id="time"),
    ],
)
async def test_discovery_without_state_uses_default(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    component: str,
    config: dict[str, Any],
    expected: str,
) -> None:
    """Without a value at discovery or a restored state, the helper default is used."""
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
    assert state.state == expected


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


DISCOVERY_VALUES = {p.values[0]: p.values[2:] for p in VALUE_ENTITIES}

RESTORED_ENTITIES = [
    pytest.param(
        "number",
        {},
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
        {},
        "restored",
        {"native_value": "restored", "native_min": 0, "native_max": 100},
        id="text",
    ),
    pytest.param("select", {"options": ["a", "b"]}, "a", {}, id="select"),
    pytest.param("time", {}, "07:30:00", {}, id="time"),
]


async def _discover_with_restored_state(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    config: dict[str, Any],
    restored: str,
    extra_data: dict[str, Any],
    discovery: dict[str, Any],
) -> State | None:
    """Discover an entity that has a restored state and return its state."""
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
            "config": {"name": "Value Entity", **config},
        }
        | discovery
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    return hass.states.get(entity_id)


@pytest.mark.parametrize(
    ("component", "config", "restored", "extra_data"), RESTORED_ENTITIES
)
async def test_restored_state_used_without_discovery_value(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    config: dict[str, Any],
    restored: str,
    extra_data: dict[str, Any],
) -> None:
    """Without a value at discovery, the restored state is used."""
    state = await _discover_with_restored_state(
        hass,
        hass_ws_client,
        component=component,
        config=config,
        restored=restored,
        extra_data=extra_data,
        discovery={},
    )
    assert state is not None
    assert state.state == restored


@pytest.mark.parametrize(
    ("component", "config", "restored", "extra_data"), RESTORED_ENTITIES
)
async def test_discovery_value_wins_over_restored_state(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    config: dict[str, Any],
    restored: str,
    extra_data: dict[str, Any],
) -> None:
    """The value sent at discovery is used instead of the restored state."""
    value, expected = DISCOVERY_VALUES[component]
    state = await _discover_with_restored_state(
        hass,
        hass_ws_client,
        component=component,
        config=config,
        restored=restored,
        extra_data=extra_data,
        discovery={"state": value},
    )
    assert state is not None
    assert state.state == expected


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        pytest.param({"max_length": 5}, "", id="max_length"),
        pytest.param({"pattern": "[0-9]+"}, STATE_UNKNOWN, id="pattern"),
    ],
)
async def test_restored_text_that_breaks_the_limits_is_dropped(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config: dict[str, Any],
    expected: str,
) -> None:
    """A restored text value the current config rejects falls back to the default."""
    state = await _discover_with_restored_state(
        hass,
        hass_ws_client,
        component="text",
        config=config,
        restored="restored",
        extra_data={"native_value": "restored", "native_min": 0, "native_max": 100},
        discovery={},
    )
    assert state is not None
    assert state.state == expected


@pytest.mark.parametrize(
    "config",
    [
        pytest.param({}, id="missing"),
        pytest.param({"options": []}, id="empty"),
    ],
)
async def test_select_discovery_without_options_is_rejected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config: dict[str, Any],
) -> None:
    """Discovery of a select without options is rejected and no entity is created."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "select",
            "server_id": "s1",
            "node_id": "n1",
            "config": {"name": "Value Entity", **config},
        }
    )
    resp = await client.receive_json()
    assert not resp["success"]
    assert resp["error"]["code"] == "invalid_format"
    await hass.async_block_till_done()

    assert hass.states.get("select.value_entity") is None


@pytest.mark.parametrize(
    ("component", "config", "value"),
    [pytest.param(*p.values[:3], id=p.id) for p in VALUE_ENTITIES],
)
@pytest.mark.parametrize(
    ("rediscovery", "available"),
    [
        pytest.param({"available": False}, False, id="unavailable"),
        pytest.param({}, True, id="no_available"),
    ],
)
async def test_rediscovery_uses_available(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    config: dict[str, Any],
    value: Any,
    rediscovery: dict[str, Any],
    available: bool,
) -> None:
    """Re-discovery of an existing entity uses available from the message."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)
    discovery = {
        "type": "nodered/discovery",
        "component": component,
        "server_id": "s1",
        "node_id": "n1",
        "config": {"name": "Value Entity", **config},
        "state": value,
    }

    await client.send_json({"id": 1} | discovery)
    assert (await client.receive_json())["success"]
    await client.send_json(
        {
            "id": 2,
            "type": "nodered/entity",
            "server_id": "s1",
            "node_id": "n1",
            "available": False,
        }
    )
    assert (await client.receive_json())["success"]

    await client.send_json({"id": 3} | discovery | rediscovery)
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    state = hass.states.get(f"{component}.value_entity")
    assert state is not None
    assert (state.state != STATE_UNAVAILABLE) is available
