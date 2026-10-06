"""Tests for the contrib version announced via nodered/version."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.nodered.const import CONF_CONTRIB_VERSION, DOMAIN
from custom_components.nodered.utils import contrib_announced_version
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_TYPE
from homeassistant.core import Event, HomeAssistant, callback


async def _setup_nodered(
    hass: HomeAssistant, data: dict | None = None
) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=data or {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _track_lifecycle_events(hass: HomeAssistant) -> list[str]:
    events: list[str] = []

    @callback
    def _listener(event: Event) -> None:
        events.append(event.data[CONF_TYPE])

    hass.bus.async_listen(DOMAIN, _listener)
    return events


async def test_announce_and_disconnect_do_not_reload_entry(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Announcing contrib_version and disconnecting must not reload the entry.

    A reload fires ``unloaded``/``loaded`` while the websocket connection stays
    open, which makes contrib register all of its nodes a second time on the
    same connection (device triggers then fire twice).
    """
    entry = await _setup_nodered(hass)
    events = _track_lifecycle_events(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.81.0"}
    )
    resp = await client.receive_json()
    assert resp["success"]
    await hass.async_block_till_done()

    assert events == []
    assert entry.state is ConfigEntryState.LOADED
    assert contrib_announced_version(hass)
    assert CONF_CONTRIB_VERSION not in entry.data

    await client.close()
    await hass.async_block_till_done()

    assert not contrib_announced_version(hass)
    assert events == []


async def test_version_probe_without_contrib_version_keeps_announce(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """A probe without contrib_version leaves a prior announce; empty clears it."""
    await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.81.0"}
    )
    assert (await client.receive_json())["success"]
    assert contrib_announced_version(hass)

    await client.send_json({"id": 2, "type": "nodered/version"})
    assert (await client.receive_json())["success"]
    assert contrib_announced_version(hass)

    await client.send_json(
        {"id": 3, "type": "nodered/version", CONF_CONTRIB_VERSION: ""}
    )
    assert (await client.receive_json())["success"]
    assert not contrib_announced_version(hass)


async def test_disconnect_only_clears_own_announce(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Closing one connection keeps the announce of another open connection."""
    await _setup_nodered(hass)
    client_a = await hass_ws_client(hass)
    client_b = await hass_ws_client(hass)

    await client_a.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.81.0"}
    )
    assert (await client_a.receive_json())["success"]
    await client_b.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.81.0"}
    )
    assert (await client_b.receive_json())["success"]

    await client_a.close()
    await hass.async_block_till_done()
    assert contrib_announced_version(hass)

    await client_b.close()
    await hass.async_block_till_done()
    assert not contrib_announced_version(hass)


async def test_announce_survives_entry_reload(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The announce belongs to the connection, so a manual reload keeps it."""
    entry = await _setup_nodered(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 1, "type": "nodered/version", CONF_CONTRIB_VERSION: "0.81.0"}
    )
    assert (await client.receive_json())["success"]

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert contrib_announced_version(hass)


async def test_stale_contrib_version_removed_without_reload(
    hass: HomeAssistant,
) -> None:
    """A contrib_version persisted by 4.3.0 is dropped from entry.data on setup."""
    events = _track_lifecycle_events(hass)
    entry = await _setup_nodered(hass, {CONF_CONTRIB_VERSION: "0.81.0"})

    assert CONF_CONTRIB_VERSION not in entry.data
    assert not contrib_announced_version(hass)
    assert events == ["loaded"]
