"""Tests for Node-RED binary sensor entity."""

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered.const import DOMAIN
from homeassistant.core import HomeAssistant


async def test_parse_state_various_inputs(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Binary sensor should interpret various state representations correctly."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    # Test various state values that should be ON
    test_cases = [
        ("1", True, "String '1' should be ON"),
        (" true ", True, "String 'true' with spaces should be ON"),
        (5, True, "Positive integer should be ON"),
        (0, False, "Zero should be OFF"),
        (None, None, "None should be None"),
        ("unknown", False, "Unknown string should be OFF"),
        (True, True, "Boolean True should be ON"),
        (False, False, "Boolean False should be OFF"),
        ("yes", True, "String 'yes' should be ON"),
        ("no", False, "String 'no' should be OFF"),
        ("open", True, "String 'open' should be ON"),
        ("home", True, "String 'home' should be ON"),
    ]

    for idx, (state_value, _expected_state, description) in enumerate(test_cases):
        # Send discovery message for binary sensor
        await client.send_json(
            {
                "id": idx + 1,
                "type": "nodered/discovery",
                "component": "binary_sensor",
                "server_id": "test-server",
                "node_id": f"test-node-{idx}",
                "state": state_value,
                "config": {"name": f"Test Binary Sensor {idx}"},
            }
        )
        resp = await client.receive_json()
        assert resp["success"], f"Failed to create entity for {description}"

    await hass.async_block_till_done()

    # Verify all entities were created with correct states
    for idx, (_state_value, expected_state, description) in enumerate(test_cases):
        entity_id = f"binary_sensor.test_binary_sensor_{idx}"
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity not found for {description}"

        if expected_state is None:
            assert state.state == "unknown", f"Failed: {description}"
        elif expected_state:
            assert state.state == "on", f"Failed: {description}"
        else:
            assert state.state == "off", f"Failed: {description}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, "on"),
        (False, "off"),
        ("yes", "on"),
        ("no", "off"),
        ("open", "on"),
        ("home", "on"),
    ],
)
async def test_parse_state_parametrized(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    value: Any,
    expected: str,
) -> None:
    """Test parametrized state values through the integration."""

    # Setup the integration
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    # Send discovery message
    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "binary_sensor",
            "server_id": "test-server",
            "node_id": "test-node",
            "state": value,
            "config": {"name": "Test Sensor"},
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    await hass.async_block_till_done()

    # Verify entity state
    entity_id = "binary_sensor.test_sensor"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == expected
