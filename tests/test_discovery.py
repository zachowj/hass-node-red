"""Tests for discovery logic."""

from typing import Any

import pytest

from custom_components.nodered.const import (
    CONF_COMPONENT,
    CONF_NODE_ID,
    CONF_REMOVE,
    CONF_SENSOR,
    CONF_SERVER_ID,
    DOMAIN_DATA,
    NODERED_DISCOVERY,
    NODERED_DISCOVERY_NEW,
    NODERED_DISCOVERY_UPDATED,
)
from custom_components.nodered.discovery import (
    ALREADY_DISCOVERED,
    start_discovery,
    stop_discovery,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)


@pytest.mark.asyncio
async def test_start_discovery_creates_and_dispatches_new(hass: HomeAssistant) -> None:
    """When a new discovery message arrives it should send a NEW signal and record discovery."""
    hass.data[DOMAIN_DATA] = {}
    await start_discovery(hass, hass.data[DOMAIN_DATA])

    events: list[Any] = []

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_SENSOR),
        lambda msg, conn: events.append((msg, conn)),
    )

    msg = {CONF_COMPONENT: CONF_SENSOR, CONF_SERVER_ID: "srv", CONF_NODE_ID: "node"}
    async_dispatcher_send(hass, NODERED_DISCOVERY, msg, object())

    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0][0] == msg

    # Discovery hash should be recorded
    discovery_hash = "nodered-srv-node"
    assert discovery_hash in hass.data[DOMAIN_DATA][ALREADY_DISCOVERED]


@pytest.mark.asyncio
async def test_start_discovery_updates_when_already_discovered(
    hass: HomeAssistant,
) -> None:
    """When a message for an already discovered device is received it should send UPDATED."""
    hass.data[DOMAIN_DATA] = {}
    discovery_hash = "nodered-srv-node2"
    hass.data[DOMAIN_DATA][ALREADY_DISCOVERED] = {discovery_hash}

    await start_discovery(hass, hass.data[DOMAIN_DATA])

    events: list[Any] = []

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_UPDATED.format(discovery_hash),
        lambda msg, conn: events.append((msg, conn)),
    )

    msg = {CONF_COMPONENT: CONF_SENSOR, CONF_SERVER_ID: "srv", CONF_NODE_ID: "node2"}
    async_dispatcher_send(hass, NODERED_DISCOVERY, msg, object())
    await hass.async_block_till_done()

    assert len(events) == 1

    # Now send with REMOVE flag - should still go to UPDATED
    msg2 = {**msg, CONF_REMOVE: True}
    async_dispatcher_send(hass, NODERED_DISCOVERY, msg2, object())
    await hass.async_block_till_done()
    assert len(events) == 2


@pytest.mark.asyncio
async def test_start_discovery_ignores_unsupported_component(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Unsupported components should be ignored and logged."""
    hass.data[DOMAIN_DATA] = {}
    await start_discovery(hass, hass.data[DOMAIN_DATA])

    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_SENSOR),
        lambda _msg, _conn: (_ for _ in ()).throw(
            AssertionError("should not be called")
        ),
    )

    msg = {CONF_COMPONENT: "unsupported", CONF_SERVER_ID: "srv", CONF_NODE_ID: "node"}
    caplog.clear()
    async_dispatcher_send(hass, NODERED_DISCOVERY, msg, object())
    await hass.async_block_till_done()

    assert "not supported" in caplog.text


@pytest.mark.asyncio
async def test_stop_discovery_unregisters(hass: HomeAssistant) -> None:
    """stop_discovery should unregister so subsequent messages don't dispatch."""
    hass.data[DOMAIN_DATA] = {}
    await start_discovery(hass, hass.data[DOMAIN_DATA])

    events: list[Any] = []
    async_dispatcher_connect(
        hass,
        NODERED_DISCOVERY_NEW.format(CONF_SENSOR),
        lambda msg, conn: events.append((msg, conn)),
    )

    # Ensure registration works
    async_dispatcher_send(
        hass,
        NODERED_DISCOVERY,
        {CONF_COMPONENT: CONF_SENSOR, CONF_SERVER_ID: "srv", CONF_NODE_ID: "n"},
        object(),
    )
    await hass.async_block_till_done()
    assert events

    # Now stop discovery and ensure no further events
    stop_discovery(hass)
    events.clear()
    async_dispatcher_send(
        hass,
        NODERED_DISCOVERY,
        {CONF_COMPONENT: CONF_SENSOR, CONF_SERVER_ID: "srv", CONF_NODE_ID: "n2"},
        object(),
    )
    await hass.async_block_till_done()
    assert not events
