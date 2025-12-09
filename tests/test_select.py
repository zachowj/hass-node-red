import pytest

from custom_components.nodered import select
from custom_components.nodered.const import CONF_SELECT, NODERED_DISCOVERY_NEW
from custom_components.nodered.select import NodeRedSelect


class FakeConnection:
    def __init__(self):
        self.sent = None

    def send_message(self, msg):
        self.sent = msg


@pytest.mark.asyncio
async def test_async_select_option_sends_message(monkeypatch):
    """async_select_option should send an event message with the selected option."""
    # Monkeypatch NodeRedEntity.__init__ to avoid parent init behavior
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda self, hass, config: None
    )
    # Monkeypatch event_message to return the payload so we can assert easily
    monkeypatch.setattr(
        select,
        "event_message",
        lambda message_id, payload: {"message_id": message_id, **payload},
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "test-msg-id"}
    node = NodeRedSelect(None, config, connection)

    await node.async_select_option("chosen-option")

    assert connection.sent is not None
    # Expect the payload contains the message id and the value/type keys
    assert connection.sent.get("message_id") == "test-msg-id"
    assert connection.sent.get(select.CONF_TYPE) == select.EVENT_VALUE_CHANGE
    # CONF_VALUE was imported into the select module
    assert connection.sent.get(select.CONF_VALUE) == "chosen-option"


def test_update_entity_state_attributes_sets_current_option(monkeypatch):
    """update_entity_state_attributes should set _attr_current_option from message state."""
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda self, hass, config: None
    )
    # Ensure parent update_entity_state_attributes does not run
    monkeypatch.setattr(
        select.NodeRedEntity,
        "update_entity_state_attributes",
        lambda self, msg: None,
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "id-1"}
    node = NodeRedSelect(None, config, connection)

    msg = {select.CONF_STATE: "option-42"}
    node.update_entity_state_attributes(msg)

    assert node._attr_current_option == "option-42"


def test_update_discovery_config_sets_icon_and_options(monkeypatch):
    """update_discovery_config should set icon and options from discovery config."""
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda self, hass, config: None
    )
    # Ensure parent update_discovery_config does not run
    monkeypatch.setattr(
        select.NodeRedEntity, "update_discovery_config", lambda self, msg: None
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "id-2"}
    node = NodeRedSelect(None, config, connection)

    discovery = {
        select.CONF_CONFIG: {
            select.CONF_ICON: "mdi:test-icon",
            select.CONF_OPTIONS: ["a", "b", "c"],
        }
    }

    node.update_discovery_config(discovery)

    assert node._attr_icon == "mdi:test-icon"
    assert node._attr_options == ["a", "b", "c"]


# Additional tests to improve coverage


# @pytest.mark.asyncio
# async def test_async_setup_entity(hass, monkeypatch):
#     """Test async_setup_entity function."""
#     add_entities_called = False
#     entity_created = False

#     # Mock functions/classes
#     async def mock_add_entities(entities_list):
#         nonlocal add_entities_called
#         add_entities_called = True
#         assert len(entities_list) == 1
#         assert isinstance(entities_list[0], NodeRedSelect)
#         nonlocal entity_created
#         entity_created = True

#     monkeypatch.setattr(
#         select.NodeRedEntity, "__init__", lambda self, hass, config: None
#     )

#     # Mock NodeRedSelect.__init__ to avoid any initialization issues
#     monkeypatch.setattr(
#         NodeRedSelect, "__init__", lambda self, hass, config, connection=None: None
#     )

#     # Test execution
#     await select._async_setup_entity(
#         hass, {select.CONF_ID: "test-id"}, mock_add_entities, FakeConnection()
#     )

#     # Ensure any callbacks have a chance to run
#     await hass.async_block_till_done()

#     # Assertions
#     assert add_entities_called
#     assert entity_created


def test_update_discovery_config_without_options_or_icon(monkeypatch):
    """update_discovery_config should handle missing icon and options gracefully."""
    monkeypatch.setattr(
        select.NodeRedEntity, "__init__", lambda self, hass, config: None
    )
    # Ensure parent update_discovery_config does not run
    monkeypatch.setattr(
        select.NodeRedEntity, "update_discovery_config", lambda self, msg: None
    )

    connection = FakeConnection()
    config = {select.CONF_ID: "id-3"}
    node = NodeRedSelect(None, config, connection)

    # Set initial values to verify they don't change
    node._attr_icon = "mdi:initial-icon"
    node._attr_options = ["initial", "options"]

    # Empty config
    discovery = {select.CONF_CONFIG: {}}

    node.update_discovery_config(discovery)

    # Icon should fall back to the SELECT_ICON from const.py
    assert node._attr_icon == select.SELECT_ICON
    # Options should remain unchanged when not specified
    assert node._attr_options == ["initial", "options"]


def test_class_attributes():
    """Test that the class has correct constant attributes."""
    # These are defined directly on the class
    assert NodeRedSelect._bidirectional is True
    assert NodeRedSelect._component == select.CONF_SELECT


# @pytest.mark.asyncio
# async def test_async_setup_entry_registers_discovery_listener(hass, monkeypatch):
#     """Test that async_setup_entry registers the proper discovery listener."""

#     # Track if dispatcher_connect was called with right parameters
#     connect_called = False
#     connect_signal = None
#     connect_target = None

#     async def mock_dispatcher_connect(hass, signal, target):
#         nonlocal connect_called, connect_signal, connect_target
#         connect_called = True
#         connect_signal = signal
#         connect_target = target
#         return lambda: None  # Return a removal function

#     # Replace the Home Assistant dispatcher_connect function that's imported in the module
#     monkeypatch.setattr(
#         "homeassistant.helpers.dispatcher.async_dispatcher_connect",
#         mock_dispatcher_connect,
#     )

#     # Call the setup
#     await select.async_setup_entry(hass, {}, None)

#     # Verify the dispatcher was connected
#     assert connect_called
#     assert connect_signal == f"{select.NODERED_DISCOVERY_NEW}.{select.CONF_SELECT}"
#     assert callable(connect_target)


async def _async_setup_entity(hass, config, async_add_entities, connection):
    """Set up a NodeRedSelect entity from discovery."""
    entity = NodeRedSelect(hass, config, connection)
    try:
        await async_add_entities([entity])
    except Exception:
        # If add_entities raises, log the error for debugging
        import logging

        logging.getLogger(__name__).exception("Failed to add entities")


async def async_setup_entry(hass, entry, async_add_entities):
    """Register discovery listener for Node-RED select entities."""
    import inspect

    from homeassistant.helpers.dispatcher import async_dispatcher_connect

    signal = f"{NODERED_DISCOVERY_NEW}.{CONF_SELECT}"

    async def _discovered(config, connection):
        await _async_setup_entity(hass, config, async_add_entities, connection)

    result = async_dispatcher_connect(hass, signal, _discovered)
    if inspect.isawaitable(result):
        await result
    return True
