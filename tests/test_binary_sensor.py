"""Tests for Node-RED binary sensor entity."""

from typing import Any

import pytest

from custom_components.nodered.binary_sensor import NodeRedBinarySensor
from homeassistant.const import CONF_STATE
from homeassistant.core import HomeAssistant


def test_parse_state_various_inputs(hass: HomeAssistant) -> None:
    """Binary sensor should interpret various state representations correctly."""
    # Strings that should be considered ON
    node = NodeRedBinarySensor(
        hass,
        {
            CONF_STATE: "1",
            "server_id": "s1",
            "node_id": "n1",
            "config": {},
        },
    )
    assert node._attr_is_on is True

    node = NodeRedBinarySensor(
        hass,
        {
            CONF_STATE: " true ",
            "server_id": "s1",
            "node_id": "n1",
            "config": {},
        },
    )
    assert node._attr_is_on is True

    node = NodeRedBinarySensor(
        hass,
        {CONF_STATE: 5, "server_id": "s1", "node_id": "n1", "config": {}},
    )
    assert node._attr_is_on is True

    node = NodeRedBinarySensor(
        hass,
        {CONF_STATE: 0, "server_id": "s1", "node_id": "n1", "config": {}},
    )
    assert node._attr_is_on is False

    node = NodeRedBinarySensor(
        hass,
        {CONF_STATE: None, "server_id": "s1", "node_id": "n1", "config": {}},
    )
    assert node._attr_is_on is None

    node = NodeRedBinarySensor(
        hass,
        {CONF_STATE: "unknown", "server_id": "s1", "node_id": "n1", "config": {}},
    )
    assert node._attr_is_on is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        ("yes", True),
        ("no", False),
        ("open", True),
        ("home", True),
    ],
)
def test_parse_state_parametrized(
    hass: HomeAssistant, value: Any, *, expected: bool
) -> None:
    node = NodeRedBinarySensor(
        hass,
        {CONF_STATE: value, "server_id": "s1", "node_id": "n1", "config": {}},
    )
    assert node._attr_is_on == expected
