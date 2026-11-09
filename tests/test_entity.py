"""Tests for NodeRedEntity core behaviors."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator
import voluptuous as vol

from custom_components.nodered.const import (
    CONF_ATTRIBUTES,
    CONF_AVAILABLE,
    CONF_COMPONENT,
    CONF_CONFIG,
    CONF_DEVICE_INFO,
    CONF_NAME,
    CONF_NODE_ID,
    CONF_OPTIONS,
    CONF_REMOVE,
    CONF_SERVER_ID,
    DOMAIN,
    DOMAIN_DATA,
)
from custom_components.nodered.discovery import (
    ALREADY_DISCOVERED,
    CHANGE_ENTITY_TYPE,
    async_discover,
    async_get_entity,
    async_register_entity,
)
from custom_components.nodered.entity import (
    NodeRedEntity,
    async_setup_discovery,
    generate_device_identifiers,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_ID,
    CONF_STATE,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from tests.helpers import FakeConnection, announce_contrib_version


class DummyEntity(NodeRedEntity):
    """A minimal subclass of NodeRedEntity for testing."""

    component = "sensor"

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        # Ensure entity_id exists to avoid hass state removal errors
        if self.entity_id is None:
            self.entity_id = f"sensor.nodered_{self._node_id}"
        # Prevent async_remove from being triggered during garbage collection
        self.platform = None  # type: ignore[assignment]


def test_update_entity_state_attributes_legacy_state_only_clears_attrs(
    hass: HomeAssistant,
) -> None:
    """Legacy: state without available injects True and clears omitted attrs."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    ent._attr_extra_state_attributes = {"keep": False}
    ent._attr_available = False
    msg = {CONF_STATE: 21.5}

    ent.update_entity_state_attributes(msg)

    assert msg[CONF_AVAILABLE] is True
    assert ent._attr_available is True
    assert ent._attr_extra_state_attributes == {}


def test_update_entity_state_attributes_presence_state_only_holds_available(
    hass: HomeAssistant,
) -> None:
    """Presence-available: state without available holds availability."""
    announce_contrib_version(hass)
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    ent._attr_extra_state_attributes = {"keep": True}
    ent._attr_available = False
    msg = {CONF_STATE: 43}

    ent.update_entity_state_attributes(msg)

    assert CONF_AVAILABLE not in msg
    assert ent._attr_available is False
    assert ent._attr_extra_state_attributes == {"keep": True}

    ent.update_entity_state_attributes({CONF_STATE: 44, CONF_ATTRIBUTES: {"unit": "C"}})

    assert ent._attr_available is False
    assert ent._attr_extra_state_attributes == {"unit": "C"}


def test_update_entity_state_attributes_legacy_state_and_attrs(
    hass: HomeAssistant,
) -> None:
    """Legacy: state + attributes applies both and injects available True."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})

    ent.update_entity_state_attributes(
        {CONF_STATE: 21.5, CONF_ATTRIBUTES: {"unit": "C"}}
    )

    assert ent._attr_available is True
    assert ent._attr_extra_state_attributes == {"unit": "C"}


def test_update_entity_state_attributes_presence_updates_only_present_keys(
    hass: HomeAssistant,
) -> None:
    """Presence-available: update only keys present; do not invent attrs."""
    announce_contrib_version(hass)
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    ent._attr_extra_state_attributes = {"prev": 1}
    ent._attr_available = True

    ent.update_entity_state_attributes({CONF_AVAILABLE: False, CONF_STATE: 18.0})

    assert ent._attr_available is False
    assert ent._attr_extra_state_attributes == {"prev": 1}

    ent.update_entity_state_attributes({CONF_AVAILABLE: True})

    assert ent._attr_available is True
    assert ent._attr_extra_state_attributes == {"prev": 1}

    ent.update_entity_state_attributes({CONF_ATTRIBUTES: {"only": "attrs"}})

    assert ent._attr_available is True
    assert ent._attr_extra_state_attributes == {"only": "attrs"}


def test_handle_lost_connection_marks_unavailable(hass: HomeAssistant) -> None:
    """Lost connection still forces unavailable."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    ent._attr_available = True
    written: list[bool] = []
    ent.async_write_ha_state = lambda: written.append(True)  # type: ignore[method-assign]

    ent.handle_lost_connection()

    assert ent._attr_available is False
    assert written == [True]


@patch("custom_components.nodered.entity.async_discover")
def test_handle_discovery_update_recreate_entity(
    mock_discover: MagicMock,
    hass: HomeAssistant,
    fake_connection: FakeConnection,
) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n1", "config": {}})
    # give the entity an id so hass.state removal won't error during teardown
    ent.entity_id = f"sensor.nodered_{ent._node_id}"
    captured: dict[str, Any] = {}

    # Capture the callback passed to async_on_remove
    def fake_async_on_remove(cb: Any) -> None:
        captured["cb"] = cb

    ent.async_on_remove = fake_async_on_remove  # type: ignore[attr-defined]
    tasks: list[Any] = []
    hass.async_create_task = tasks.append  # type: ignore[attr-defined]

    msg = {CONF_REMOVE: CHANGE_ENTITY_TYPE, CONF_COMPONENT: "switch", CONF_ID: "mid"}
    ent.handle_discovery_update(msg, fake_connection)

    # async_on_remove should have been called with a recreate callback
    assert "cb" in captured
    assert callable(captured["cb"])
    # A task scheduling the entity removal should have been created
    assert tasks
    assert hasattr(tasks[0], "__await__")
    tasks[0].close()
    # discovery not run yet — recreate_entity will run when the
    # on_remove callback is invoked
    mock_discover.assert_not_called()


def test_handle_discovery_update_remove_schedules_removal(hass: HomeAssistant) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n2", "config": {}})
    tasks: list[Any] = []
    hass.async_create_task = tasks.append  # type: ignore[attr-defined]

    msg = {CONF_REMOVE: True}
    ent.handle_discovery_update(msg, None)  # type: ignore[arg-type]

    # Permanent remove must schedule MQTT-style registry+state cleanup
    assert tasks
    assert hasattr(tasks[0], "__await__")
    tasks[0].close()


@pytest.mark.asyncio
async def test_async_remove_from_hass_removes_registry_entry(
    hass: HomeAssistant,
) -> None:
    """Registered entities must be deleted from the entity registry."""
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "reg", "config": {}})
    ent.entity_id = "sensor.nodered_reg"

    registry = MagicMock()
    registry.async_get.return_value = MagicMock()
    ent.async_remove = AsyncMock()  # type: ignore[method-assign]

    with patch(
        "custom_components.nodered.entity.async_get",
        return_value=registry,
    ):
        await ent._async_remove_from_hass()

    registry.async_remove.assert_called_once_with("sensor.nodered_reg")
    ent.async_remove.assert_not_called()


@pytest.mark.asyncio
async def test_async_remove_from_hass_force_removes_unregistered(
    hass: HomeAssistant,
) -> None:
    """Unregistered entities must force-remove state."""
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "unreg", "config": {}})
    ent.entity_id = "sensor.nodered_unreg"
    ent.async_remove = AsyncMock()  # type: ignore[method-assign]

    with patch(
        "custom_components.nodered.entity.async_get",
        return_value=MagicMock(async_get=MagicMock(return_value=None)),
    ):
        await ent._async_remove_from_hass()

    ent.async_remove.assert_awaited_once_with(force_remove=True)


def test_handle_discovery_update_bidirectional_sets_connection_subscription(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n3", "config": {}})
    ent.entity_id = f"sensor.nodered_{ent._node_id}"
    ent._bidirectional = True
    msg = {CONF_CONFIG: {}, CONF_ID: "msg-1"}
    ent.handle_discovery_update(msg, fake_connection)
    assert ent._attr_available is True
    assert getattr(ent, "_message_id", None) == "msg-1"
    assert fake_connection.subscriptions.get("msg-1") == ent.handle_lost_connection


def test_update_discovery_config_sets_attributes(hass: HomeAssistant) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n4", "config": {}})
    ent.entity_id = f"sensor.nodered_{ent._node_id}"
    cfg = {
        CONF_CONFIG: {
            CONF_NAME: "MyName",
            CONF_ICON: "mdi:test",
            CONF_ENTITY_CATEGORY: "config",
            CONF_UNIT_OF_MEASUREMENT: "m",
            CONF_DEVICE_CLASS: "temp",
        }
    }
    ent.update_discovery_config(cfg)
    assert ent._attr_name == "MyName"
    assert ent._attr_icon == "mdi:test"
    assert ent._attr_unit_of_measurement == "m"
    assert ent._attr_entity_category == EntityCategory.CONFIG


def test_handle_config_update_writes_state(hass: HomeAssistant) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n5", "config": {}})
    # set entity_id to avoid async_write_ha_state errors during tests
    ent.entity_id = f"sensor.nodered_{ent._node_id}"
    cfg = {
        CONF_CONFIG: {
            CONF_NAME: "NewName",
            CONF_ICON: "mdi:new",
            CONF_OPTIONS: {"opt": 1},
        }
    }
    ent.handle_config_update(cfg)
    assert ent._attr_name == "NewName"
    assert ent._attr_icon == "mdi:new"
    assert getattr(ent, "_attr_options", None) == {"opt": 1}


def test_update_discovery_device_info_raises_when_unique_id_missing(
    hass: HomeAssistant,
) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n6", "config": {}})
    # Force unique_id to None to test the validation branch
    ent._attr_unique_id = None
    with pytest.raises(RuntimeError):
        ent.update_discovery_device_info({})


def test_missing_component_raises_type_error(
    hass: HomeAssistant,
) -> None:
    """Ensure subclasses without `component` raise a TypeError on init."""

    class BadEntity(NodeRedEntity):
        """Subclass that forgets to set `component`."""

    with pytest.raises(TypeError):
        BadEntity(hass, {CONF_SERVER_ID: "server-1", CONF_NODE_ID: "node-1"})  # pyright: ignore[reportArgumentType]


def test_missing_ids_raises_type_error(
    hass: HomeAssistant,
) -> None:
    """Ensure missing `server_id` or `node_id` raises a TypeError."""

    class GoodEntity(NodeRedEntity):
        component = "sensor"

    with pytest.raises(TypeError, match="requires 'server_id' and 'node_id'"):
        GoodEntity(hass, {})  # pyright: ignore[reportArgumentType] # no ids

    with pytest.raises(TypeError, match="requires 'server_id' and 'node_id'"):
        GoodEntity(hass, {CONF_SERVER_ID: "s1"})  # pyright: ignore[reportArgumentType] # missing node id


class BidirectionalEntity(NodeRedEntity):
    """Bidirectional entity that relies on the base class constructor."""

    _bidirectional = True
    component = "switch"


def test_bidirectional_without_connection_raises_type_error(
    hass: HomeAssistant,
) -> None:
    """Ensure a bidirectional entity cannot be created without a connection."""
    config = {CONF_ID: "msg-1", CONF_SERVER_ID: "s1", CONF_NODE_ID: "n1", "config": {}}

    with pytest.raises(TypeError, match="requires a connection"):
        BidirectionalEntity(hass, config)


def test_bidirectional_stores_message_id_and_connection(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """Ensure the base class stores the message id and connection."""
    config = {CONF_ID: "msg-1", CONF_SERVER_ID: "s1", CONF_NODE_ID: "n1", "config": {}}

    ent = BidirectionalEntity(hass, config, fake_connection)

    assert ent._message_id == "msg-1"
    assert ent._connection is fake_connection


async def test_async_setup_discovery_adds_entity(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    """Ensure a discovery for the class's component adds a new entity."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    added: list[Entity] = []

    def add_entities(entities: list[Entity], _update_before_add: bool = False) -> None:
        added.extend(entities)

    hass.data[DOMAIN_DATA] = {}
    async_setup_discovery(hass, config_entry, BidirectionalEntity, add_entities)  # pyright: ignore[reportArgumentType]
    config = {
        CONF_ID: "msg-1",
        CONF_COMPONENT: "switch",
        CONF_SERVER_ID: "s1",
        CONF_NODE_ID: "n1",
        "config": {},
    }
    async_discover(hass, config, fake_connection)

    assert len(added) == 1
    assert isinstance(added[0], BidirectionalEntity)
    assert added[0]._connection is fake_connection


def test_generate_device_identifiers_returns_correct_format() -> None:
    """Test generate_device_identifiers returns proper identifiers set."""
    device_id = "test-device-123"
    result = generate_device_identifiers(device_id)

    assert isinstance(result, set)
    assert len(result) == 1
    assert (DOMAIN, device_id) in result


def test_generate_device_identifiers_with_special_characters() -> None:
    """Test generate_device_identifiers handles special characters."""
    device_id = "device:with-special_chars.test"
    result = generate_device_identifiers(device_id)

    assert len(result) == 1
    assert (DOMAIN, device_id) in result


def test_generate_device_identifiers_with_empty_string() -> None:
    """Test generate_device_identifiers handles empty string."""
    device_id = ""
    result = generate_device_identifiers(device_id)

    assert len(result) == 1
    assert (DOMAIN, "") in result


def test_generate_device_identifiers_uniqueness() -> None:
    """Test generate_device_identifiers creates unique sets for different IDs."""
    id1 = generate_device_identifiers("device-1")
    id2 = generate_device_identifiers("device-2")

    assert id1 != id2
    assert len(id1.intersection(id2)) == 0


def test_init_minimal_config(hass: HomeAssistant) -> None:
    """Test initialization with minimal required config."""
    config = {
        CONF_SERVER_ID: "test-server",
        CONF_NODE_ID: "test-node",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    assert ent._server_id == "test-server"
    assert ent._node_id == "test-node"
    assert ent._attr_unique_id == f"{DOMAIN}-test-server-test-node"
    assert ent._attr_should_poll is False
    assert ent._attr_device_info is None


def test_init_with_full_device_info(hass: HomeAssistant) -> None:
    """Test initialization with complete device info creates DeviceInfo."""
    config = {
        CONF_SERVER_ID: "srv1",
        CONF_NODE_ID: "node1",
        CONF_CONFIG: {},
        CONF_DEVICE_INFO: {
            "id": "device-123",
            "hw_version": "1.0",
            "manufacturer": "Test Corp",
            "model": "Test Model",
            "name": "Test Device",
            "sw_version": "2.0",
        },
    }
    ent = DummyEntity(hass, config)

    assert ent._attr_device_info is not None
    assert ent._attr_device_info.get("identifiers") == {(DOMAIN, "device-123")}
    assert ent._attr_device_info.get("hw_version") == "1.0"
    assert ent._attr_device_info.get("manufacturer") == "Test Corp"
    assert ent._attr_device_info.get("model") == "Test Model"
    assert ent._attr_device_info.get("name") == "Test Device"
    assert ent._attr_device_info.get("sw_version") == "2.0"


@pytest.mark.filterwarnings(
    "ignore:coroutine 'Entity.async_remove' was never awaited:RuntimeWarning"
)
def test_init_with_partial_device_info(hass: HomeAssistant) -> None:
    """Test initialization with partial device info."""
    config = {
        CONF_SERVER_ID: "srv2",
        CONF_NODE_ID: "node2",
        CONF_CONFIG: {},
        CONF_DEVICE_INFO: {
            "id": "device-456",
            "name": "Partial Device",
        },
    }
    ent = DummyEntity(hass, config)

    assert ent._attr_device_info is not None
    assert ent._attr_device_info.get("identifiers") == {(DOMAIN, "device-456")}
    assert ent._attr_device_info.get("name") == "Partial Device"
    # Optional fields should be None
    assert ent._attr_device_info.get("hw_version") is None
    assert ent._attr_device_info.get("manufacturer") is None
    assert ent._attr_device_info.get("model") is None
    assert ent._attr_device_info.get("sw_version") is None


def test_init_without_device_info(hass: HomeAssistant) -> None:
    """Test initialization without device_info leaves it as None."""
    config = {
        CONF_SERVER_ID: "srv3",
        CONF_NODE_ID: "node3",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    assert ent._attr_device_info is None


def test_init_with_empty_device_info(hass: HomeAssistant) -> None:
    """Test initialization with empty device_info dict (no id)."""
    config = {
        CONF_SERVER_ID: "srv4",
        CONF_NODE_ID: "node4",
        CONF_CONFIG: {},
        CONF_DEVICE_INFO: {},
    }
    ent = DummyEntity(hass, config)

    assert ent._attr_device_info is None


def test_init_unique_id_format(hass: HomeAssistant) -> None:
    """Test that unique_id follows expected format."""
    config = {
        CONF_SERVER_ID: "my-server",
        CONF_NODE_ID: "my-node",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    expected_id = f"{DOMAIN}-my-server-my-node"
    assert ent.unique_id == expected_id
    assert ent._attr_unique_id == expected_id


@patch.object(DummyEntity, "update_entity_state_attributes")
@patch.object(DummyEntity, "update_discovery_config")
def test_init_calls_update_methods(
    mock_discovery: Any,
    mock_attributes: Any,
    hass: HomeAssistant,
) -> None:
    """Test that __init__ calls update_discovery_config and update_entity_state_attributes."""
    config = {
        CONF_SERVER_ID: "srv5",
        CONF_NODE_ID: "node5",
        CONF_CONFIG: {CONF_NAME: "Test Entity"},
        CONF_ATTRIBUTES: {"attr1": "value1"},
    }

    ent = DummyEntity(hass, config)

    # Both methods should have been called during init
    mock_discovery.assert_called_once()
    mock_attributes.assert_called_once()
    # Verify the entity was created
    assert ent._server_id == "srv5"
    assert ent._node_id == "node5"


async def test_async_added_to_hass_registers_entity(hass: HomeAssistant) -> None:
    """Test that async_added_to_hass routes the node's messages to the entity."""
    ent = DummyEntity(
        hass, {CONF_SERVER_ID: "srv-add", CONF_NODE_ID: "node-add", CONF_CONFIG: {}}
    )

    await ent.async_added_to_hass()

    assert async_get_entity(hass, "srv-add", "node-add") is ent


async def test_aborted_add_unregisters_entity_and_forgets_discovery(
    hass: HomeAssistant,
) -> None:
    """Ensure an aborted add leaves no routing or discovery hash behind."""
    ent = DummyEntity(
        hass, {CONF_SERVER_ID: "srv-rm", CONF_NODE_ID: "node-rm", CONF_CONFIG: {}}
    )
    hass.data.setdefault(DOMAIN_DATA, {})[ALREADY_DISCOVERED] = {ent.unique_id}
    await ent.async_added_to_hass()

    # HA 2026.10+ aborts the add when the first state write fails
    ent.add_to_platform_abort()

    assert async_get_entity(hass, "srv-rm", "node-rm") is None
    assert ent.unique_id not in hass.data[DOMAIN_DATA][ALREADY_DISCOVERED]


async def test_add_aborted_before_added_forgets_discovery(
    hass: HomeAssistant,
) -> None:
    """Ensure the hash is forgotten when the add aborts before it is added."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    hass.data.setdefault(DOMAIN_DATA, {})[ALREADY_DISCOVERED] = {ent.unique_id}

    ent.add_to_platform_abort()

    assert ent.unique_id not in hass.data[DOMAIN_DATA][ALREADY_DISCOVERED]


async def test_removing_old_entity_keeps_replacement_registered(
    hass: HomeAssistant,
) -> None:
    """Ensure removing an old entity leaves its replacement registered."""
    config = {CONF_SERVER_ID: "srv-new", CONF_NODE_ID: "node-new", CONF_CONFIG: {}}
    old = DummyEntity(hass, config)
    new = DummyEntity(hass, config)
    await old.async_added_to_hass()
    async_register_entity(hass, new)

    old.add_to_platform_abort()

    assert async_get_entity(hass, "srv-new", "node-new") is new


async def test_removed_entity_is_rediscovered(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Ensure discovery recreates an entity that was removed from HA."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    discovery = {
        "type": "nodered/discovery",
        "component": "sensor",
        "server_id": "s1",
        "node_id": "n1",
        "state": "on",
    }
    entity_registry = er.async_get(hass)

    await client.send_json({"id": 1, **discovery})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, "nodered-s1-n1")
    assert entity_id is not None

    entity_registry.async_remove(entity_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id) is None

    await client.send_json({"id": 2, **discovery})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, "nodered-s1-n1")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"


def test_update_config_no_changes(hass: HomeAssistant) -> None:
    """update_config should leave attributes unchanged when no config present."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    # Seed attributes
    ent._attr_name = "Original"
    ent._attr_icon = "mdi:original"
    ent._attr_entity_picture = "orig.png"
    ent._attr_options = {"k": 1}

    # Call with empty message and with a message missing CONF_CONFIG
    ent.update_config({})
    assert ent._attr_name == "Original"
    assert ent._attr_icon == "mdi:original"
    assert ent._attr_entity_picture == "orig.png"
    assert ent._attr_options == {"k": 1}

    ent.update_config({"other": "value"})
    assert ent._attr_name == "Original"
    assert ent._attr_icon == "mdi:original"
    assert ent._attr_entity_picture == "orig.png"
    assert ent._attr_options == {"k": 1}


def test_update_config_updates_fields(hass: HomeAssistant) -> None:
    """update_config should apply provided config updates."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})

    cfg = {
        CONF_CONFIG: {
            CONF_NAME: "NewName",
            CONF_ICON: "mdi:new",
            CONF_OPTIONS: {"opt": True},
        }
    }
    ent.update_config(cfg)

    assert ent._attr_name == "NewName"
    assert ent._attr_icon == "mdi:new"
    assert getattr(ent, "_attr_options", None) == {"opt": True}


def test_update_config_ignores_empty_values(hass: HomeAssistant) -> None:
    """update_config should not overwrite attributes with falsy/empty values."""
    ent = DummyEntity(hass, {CONF_SERVER_ID: "s", CONF_NODE_ID: "n", CONF_CONFIG: {}})
    # Seed attributes with non-empty values
    ent._attr_name = "KeepName"
    ent._attr_icon = "mdi:keep"
    ent._attr_entity_picture = "keep.png"
    ent._attr_options = {"keep": 1}

    cfg = {
        CONF_CONFIG: {
            CONF_NAME: "",
            CONF_ICON: "",
            CONF_OPTIONS: {},  # empty dict is falsy and should not overwrite
        }
    }
    ent.update_config(cfg)

    assert ent._attr_name == "KeepName"
    assert ent._attr_icon == "mdi:keep"
    assert ent._attr_options == {"keep": 1}


async def _setup_ws_client(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> Any:
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return await hass_ws_client(hass)


REJECTED_STATE_CASES = [
    pytest.param(
        "sensor",
        {"state": 21.5, "config": {"name": "Temp", "unit_of_measurement": "°C"}},
        "21.5",
        "not a number",
        "non-numeric value",
        id="numeric_sensor",
    ),
    pytest.param(
        "sensor",
        {"state": "short", "config": {"name": "Temp"}},
        "short",
        "x" * 256,
        "longer than 255 characters",
        id="sensor_over_255_characters",
    ),
]


@pytest.mark.parametrize(
    ("component", "discovery", "old_state", "new_state", "error"),
    REJECTED_STATE_CASES,
)
async def test_rejected_update_is_returned_and_undone(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    component: str,
    discovery: dict[str, Any],
    old_state: str,
    new_state: Any,
    error: str,
) -> None:
    """An update HA rejects gets an error reply and leaves the entity as it was."""
    entity_id = f"{component}.temp"
    client = await _setup_ws_client(hass, hass_ws_client)
    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": component,
            "server_id": "s1",
            "node_id": "n1",
            "attributes": {"room": "kitchen"},
            **discovery,
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    entity_update = {"type": "nodered/entity", "server_id": "s1", "node_id": "n1"}

    await client.send_json(
        {
            "id": 2,
            **entity_update,
            "state": new_state,
            "attributes": {"room": "lounge"},
        }
    )
    resp = await client.receive_json()

    assert not resp["success"]
    assert resp["error"]["code"] == "invalid_format"
    assert error in resp["error"]["message"]
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == old_state
    assert state.attributes["room"] == "kitchen"

    # Would fail too if the rejected state had been kept
    await client.send_json({"id": 3, **entity_update, "available": False})
    assert (await client.receive_json())["success"]
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unavailable"


async def test_unexpected_update_error_is_returned(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """An unexpected exception during an update is not acknowledged as success."""
    client = await _setup_ws_client(hass, hass_ws_client)
    await client.send_json(
        {
            "id": 1,
            "type": "nodered/discovery",
            "component": "sensor",
            "server_id": "s1",
            "node_id": "n1",
            "state": 1,
        }
    )
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()

    with patch.object(NodeRedEntity, "validate_state", side_effect=RuntimeError):
        await client.send_json(
            {
                "id": 2,
                "type": "nodered/entity",
                "server_id": "s1",
                "node_id": "n1",
                "state": 2,
            }
        )
        resp = await client.receive_json()

    assert not resp["success"]
    assert resp["error"]["code"] == "unknown_error"


UNDO_CASES = [
    pytest.param("binary_sensor", {"state": True}, False, id="binary_sensor"),
    pytest.param("button", {}, None, id="button"),
    pytest.param("number", {"state": 5}, 7, id="number"),
    pytest.param(
        "select", {"state": "a", "config": {"options": ["a", "b"]}}, "b", id="select"
    ),
    pytest.param("sensor", {"state": 21.5}, 22, id="sensor"),
    pytest.param("switch", {"state": True}, False, id="switch"),
    pytest.param("text", {"state": "hi"}, "bye", id="text"),
    pytest.param("time", {"state": "12:34:00"}, "13:00:00", id="time"),
]


def _attrs(entity: NodeRedEntity) -> dict[str, Any]:
    return {
        name: getattr(entity, name, None)
        for name in dir(entity)
        if name.startswith("_attr_")
    }


@pytest.mark.parametrize(("component", "fields", "new_state"), UNDO_CASES)
async def test_rejected_update_restores_every_changed_attribute(
    hass: HomeAssistant, component: str, fields: dict[str, Any], new_state: Any
) -> None:
    """Every attribute an entity update can change is in update_attrs."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    async_discover(
        hass,
        {
            "id": 1,
            CONF_COMPONENT: component,
            CONF_SERVER_ID: "s1",
            CONF_NODE_ID: "n1",
            **fields,
            CONF_CONFIG: {CONF_NAME: "Undo", **fields.get(CONF_CONFIG, {})},
        },
        FakeConnection(),
    )
    entity = async_get_entity(hass, "s1", "n1")
    assert entity is not None
    before = _attrs(entity)
    entity_msg = {
        CONF_STATE: new_state,
        CONF_ATTRIBUTES: {"changed": True},
        CONF_AVAILABLE: False,
    }

    with (
        patch.object(entity, "validate_state", side_effect=vol.Invalid("rejected")),
        pytest.raises(vol.Invalid),
    ):
        entity.handle_entity_update(entity_msg)

    assert _attrs(entity) == before
