"""Unit tests for Node-RED binary sensor availability semantics."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered.binary_sensor import NodeRedBinarySensor
from custom_components.nodered.const import (
    CONF_AVAILABLE,
    CONF_CONFIG,
    CONF_CONTRIB_VERSION,
    DOMAIN,
)
from homeassistant.const import CONF_STATE
from homeassistant.core import HomeAssistant


def test_binary_sensor_discovered_without_state_legacy_is_unknown(
    hass: HomeAssistant,
) -> None:
    """Without presence-available: discovery without state stays Unknown."""
    node = NodeRedBinarySensor(
        hass, {"server_id": "s1", "node_id": "bs-no-state", CONF_CONFIG: {}}
    )
    assert node._attr_available is True
    assert node._attr_is_on is None


def test_binary_sensor_discovered_without_state_presence_is_unavailable(
    hass: HomeAssistant,
) -> None:
    """With presence-available: discovery without state is Unavailable."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_CONTRIB_VERSION: "0.80.3"})
    entry.add_to_hass(hass)
    node = NodeRedBinarySensor(
        hass, {"server_id": "s1", "node_id": "bs-no-state-new", CONF_CONFIG: {}}
    )
    assert node._attr_available is False
    assert node._attr_is_on is None


def test_binary_sensor_discovered_with_state_is_available(hass: HomeAssistant) -> None:
    """Discovery with state comes up available."""
    node = NodeRedBinarySensor(
        hass,
        {
            "server_id": "s1",
            "node_id": "bs-with-state",
            CONF_CONFIG: {},
            CONF_STATE: True,
        },
    )
    assert node._attr_available is True
    assert node._attr_is_on is True


def test_binary_sensor_preserves_is_on_when_state_omitted(hass: HomeAssistant) -> None:
    """Availability-only updates must not clear is_on."""
    node = NodeRedBinarySensor(
        hass,
        {
            "server_id": "s1",
            "node_id": "bs-preserve",
            CONF_CONFIG: {},
            CONF_STATE: True,
        },
    )
    assert node._attr_is_on is True

    node.update_entity_state_attributes({CONF_AVAILABLE: False})

    assert node._attr_available is False
    assert node._attr_is_on is True
