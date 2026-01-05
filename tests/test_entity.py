"""Tests for NodeRedEntity core behaviors."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import pytest

from custom_components.nodered.const import (
    CONF_ATTRIBUTES,
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
    NODERED_CONFIG_UPDATE,
    NODERED_DISCOVERY_UPDATED,
    NODERED_ENTITY,
)
from custom_components.nodered.discovery import ALREADY_DISCOVERED, CHANGE_ENTITY_TYPE
from custom_components.nodered.entity import NodeRedEntity, generate_device_identifiers
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_ID,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from tests.helpers import FakeConnection


class DummyEntity(NodeRedEntity):
    """A minimal subclass of NodeRedEntity for testing."""

    component = "sensor"

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        # Ensure removal signal attributes exist for hass teardown
        self._remove_signal_entity_update: Callable[[], None] | None = None
        self._remove_signal_discovery_update: Callable[[], None] | None = None
        self._remove_signal_config_update: Callable[[], None] | None = None
        # Ensure entity_id exists to avoid hass state removal errors
        if self.entity_id is None:
            self.entity_id = f"sensor.nodered_{self._node_id}"
        # Prevent async_remove from being triggered during garbage collection
        self.platform = None  # type: ignore[assignment]


def test_handle_discovery_update_recreate_entity(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
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
    hass.async_create_task = lambda coro: tasks.append(coro)  # type: ignore[attr-defined]

    sent: list[tuple] = []
    monkeypatch.setattr(
        "homeassistant.helpers.dispatcher.async_dispatcher_send",
        lambda _h, sig, msg, conn=None: sent.append((sig, msg, conn)),
    )

    msg = {CONF_REMOVE: CHANGE_ENTITY_TYPE, CONF_COMPONENT: "switch", CONF_ID: "mid"}
    ent.handle_discovery_update(msg, fake_connection)

    # async_on_remove should have been called with a recreate callback
    assert "cb" in captured
    assert callable(captured["cb"])
    # A task scheduling the entity removal should have been created
    assert tasks
    assert hasattr(tasks[0], "__await__")
    # dispatcher_send not executed yet — recreate_entity will run when the
    # on_remove callback is invoked
    assert not sent


def test_handle_discovery_update_cleanup_discovery(hass: HomeAssistant) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n2", "config": {}})
    # ensure teardown won't fail when hass removes entities
    ent._remove_signal_entity_update = None
    ent._remove_signal_discovery_update = None
    ent._remove_signal_config_update = None
    # Prepare discovery tracking with the entity present
    hass.data.setdefault(DOMAIN_DATA, {})[ALREADY_DISCOVERED] = {
        ent.unique_id: {"x": 1}
    }

    captured: dict[str, Any] = {}

    def fake_async_on_remove(cb: Any) -> None:
        captured["cb"] = cb

    ent.async_on_remove = fake_async_on_remove  # type: ignore[attr-defined]

    msg = {CONF_REMOVE: "permanent"}
    ent.handle_discovery_update(msg, None)  # type: ignore[arg-type]

    # Call the registered cleanup callback and assert it removes discovery entry
    assert "cb" in captured
    assert callable(captured["cb"])
    captured["cb"]()
    assert ent.unique_id not in hass.data[DOMAIN_DATA].get(ALREADY_DISCOVERED, {})


def test_handle_discovery_update_bidirectional_sets_connection_subscription(
    hass: HomeAssistant, fake_connection: FakeConnection
) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n3", "config": {}})
    # avoid hass teardown issues
    ent._remove_signal_entity_update = None
    ent._remove_signal_discovery_update = None
    ent._remove_signal_config_update = None
    ent.entity_id = f"sensor.nodered_{ent._node_id}"
    ent._bidirectional = True
    msg = {CONF_CONFIG: {}, CONF_ID: "msg-1"}
    ent.handle_discovery_update(msg, fake_connection)
    assert ent._attr_available is True
    assert getattr(ent, "_message_id", None) == "msg-1"
    assert fake_connection.subscriptions.get("msg-1") == ent.handle_lost_connection


def test_update_discovery_config_sets_attributes(hass: HomeAssistant) -> None:
    ent = DummyEntity(hass, {"server_id": "s", "node_id": "n4", "config": {}})
    ent._remove_signal_entity_update = None
    ent._remove_signal_discovery_update = None
    ent._remove_signal_config_update = None
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
    ent._remove_signal_entity_update = None
    ent._remove_signal_discovery_update = None
    ent._remove_signal_config_update = None
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


def test_init_calls_update_methods(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that __init__ calls update_discovery_config and update_entity_state_attributes."""
    config = {
        CONF_SERVER_ID: "srv5",
        CONF_NODE_ID: "node5",
        CONF_CONFIG: {CONF_NAME: "Test Entity"},
        CONF_ATTRIBUTES: {"attr1": "value1"},
    }

    calls: list[str] = []

    original_update_discovery = DummyEntity.update_discovery_config
    original_update_attributes = DummyEntity.update_entity_state_attributes

    def track_discovery(self: DummyEntity, msg: dict[str, Any]) -> None:
        calls.append("discovery")
        original_update_discovery(self, msg)

    def track_attributes(self: DummyEntity, msg: dict[str, Any]) -> None:
        calls.append("attributes")
        original_update_attributes(self, msg)

    monkeypatch.setattr(DummyEntity, "update_discovery_config", track_discovery)
    monkeypatch.setattr(DummyEntity, "update_entity_state_attributes", track_attributes)

    ent = DummyEntity(hass, config)

    # Both methods should have been called during init
    assert "discovery" in calls
    assert "attributes" in calls
    # Verify the config was actually applied
    assert ent._attr_name == "Test Entity"
    assert ent._attr_extra_state_attributes == {"attr1": "value1"}


def test_async_added_to_hass_registers_all_signals(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that async_added_to_hass registers all three dispatcher signals."""
    config = {
        CONF_SERVER_ID: "srv-add",
        CONF_NODE_ID: "node-add",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    # Track all calls to async_dispatcher_connect
    registered: list[tuple[str, Any]] = []

    def fake_connect(hass: HomeAssistant, signal: str, callback: Any) -> Any:
        """Capture signal and callback, return a fake removal function."""
        registered.append((signal, callback))
        return lambda: None  # return a no-op removal callable

    monkeypatch.setattr(
        "custom_components.nodered.entity.async_dispatcher_connect",
        fake_connect,
    )

    # Run async_added_to_hass
    hass.loop.run_until_complete(ent.async_added_to_hass())

    # Should have registered exactly 3 signals
    assert len(registered) == 3

    # Extract signals and callbacks
    signals = [sig for sig, _ in registered]
    callbacks = [cb for _, cb in registered]

    # Verify the correct signals were registered
    assert NODERED_ENTITY.format("srv-add", "node-add") in signals
    assert NODERED_DISCOVERY_UPDATED.format(ent.unique_id) in signals
    assert NODERED_CONFIG_UPDATE.format("srv-add", "node-add") in signals

    # Verify the correct callbacks were registered
    assert ent.handle_entity_update in callbacks
    assert ent.handle_discovery_update in callbacks
    assert ent.handle_config_update in callbacks


def test_async_added_to_hass_stores_removal_callbacks(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that async_added_to_hass stores removal callbacks in instance attributes."""
    config = {
        CONF_SERVER_ID: "srv-store",
        CONF_NODE_ID: "node-store",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    # Create unique removal functions so we can verify they're stored correctly
    removal_fns: dict[str, Any] = {}

    def fake_connect(hass: HomeAssistant, signal: str, callback: Any) -> Any:
        """Return a unique removal function for each signal."""
        removal_fn = lambda sig=signal: f"removed_{sig}"  # noqa: E731
        removal_fns[signal] = removal_fn
        return removal_fn

    monkeypatch.setattr(
        "custom_components.nodered.entity.async_dispatcher_connect",
        fake_connect,
    )

    # Run async_added_to_hass
    hass.loop.run_until_complete(ent.async_added_to_hass())

    # Verify removal callbacks are stored in the correct attributes
    entity_signal = NODERED_ENTITY.format("srv-store", "node-store")
    discovery_signal = NODERED_DISCOVERY_UPDATED.format(ent.unique_id)
    config_signal = NODERED_CONFIG_UPDATE.format("srv-store", "node-store")

    assert ent._remove_signal_entity_update is removal_fns[entity_signal]
    assert ent._remove_signal_discovery_update is removal_fns[discovery_signal]
    assert ent._remove_signal_config_update is removal_fns[config_signal]


def test_async_will_remove_from_hass_calls_all_removals(
    hass: HomeAssistant,
) -> None:
    """Test that async_will_remove_from_hass calls all removal callbacks."""
    config = {
        CONF_SERVER_ID: "srv-remove",
        CONF_NODE_ID: "node-remove",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    # Track which removal functions were called
    called: list[str] = []

    ent._remove_signal_entity_update = cast(
        Callable[[], None], lambda: called.append("entity")
    )
    ent._remove_signal_discovery_update = cast(
        Callable[[], None], lambda: called.append("discovery")
    )
    ent._remove_signal_config_update = cast(
        Callable[[], None], lambda: called.append("config")
    )

    # Run async_will_remove_from_hass
    hass.loop.run_until_complete(ent.async_will_remove_from_hass())

    # All three removal callbacks should have been called
    assert "entity" in called
    assert "discovery" in called
    assert "config" in called
    assert len(called) == 3


def test_async_will_remove_from_hass_handles_none_removals(
    hass: HomeAssistant,
) -> None:
    """Test that async_will_remove_from_hass handles None removal callbacks gracefully."""
    config = {
        CONF_SERVER_ID: "srv-none",
        CONF_NODE_ID: "node-none",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    # Explicitly set removal callbacks to None
    ent._remove_signal_entity_update = None
    ent._remove_signal_discovery_update = None
    ent._remove_signal_config_update = None

    # Should not raise an exception
    hass.loop.run_until_complete(ent.async_will_remove_from_hass())


def test_async_will_remove_from_hass_partial_removals(
    hass: HomeAssistant,
) -> None:
    """Test async_will_remove_from_hass with some removal callbacks set and others None."""
    config = {
        CONF_SERVER_ID: "srv-partial",
        CONF_NODE_ID: "node-partial",
        CONF_CONFIG: {},
    }
    ent = DummyEntity(hass, config)

    called: list[str] = []

    # Set only some removal callbacks
    ent._remove_signal_entity_update = cast(
        Callable[[], None], lambda: called.append("entity")
    )
    ent._remove_signal_discovery_update = None
    ent._remove_signal_config_update = cast(
        Callable[[], None], lambda: called.append("config")
    )

    # Run async_will_remove_from_hass
    hass.loop.run_until_complete(ent.async_will_remove_from_hass())

    # Only the non-None callbacks should have been called
    assert "entity" in called
    assert "config" in called
    assert "discovery" not in called
    assert len(called) == 2


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
