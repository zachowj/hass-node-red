"""Helpers for testing Node-RED Home Assistant integration.

Provides fake connection classes and utilities for test cases.
"""

from collections.abc import Callable, Hashable
import contextlib
from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered.const import DOMAIN
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.messages import (
    error_message,
    event_message,
    result_message,
)
from homeassistant.core import Context
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity_registry import RegistryEntry


class FakeConnection(ActiveConnection):
    """A Fake ActiveConnection-compatible connection for tests."""

    def __init__(self) -> None:
        self.sent: Any = None
        # subscriptions map message ids to removal callbacks
        self.subscriptions: dict[Hashable, Callable[[], Any]] = {}
        # mimic an admin user required by the websocket decorators
        self.user = type("U", (), {"is_admin": True})
        self.last_id = 0
        self.can_coalesce = False
        self.supported_features: dict[str, float] = {}

    def send_message(self, msg: dict[str, Any]) -> None:
        """Store the message that would be sent over the websocket."""
        self.sent = msg

    def send_result(self, msg_id: int, result: Any | None = None) -> None:
        """Send a websocket result message."""
        self.send_message(result_message(msg_id, result))

    def send_event(self, msg_id: int, event: Any | None = None) -> None:
        """Send a websocket event message."""
        self.send_message(event_message(msg_id, event))

    def send_error(
        self,
        msg_id: int,
        code: str,
        message: str,
        translation_key: str | None = None,
        translation_domain: str | None = None,
        translation_placeholders: dict[str, Any] | None = None,
    ) -> None:
        """Send a websocket error message."""
        self.send_message(
            error_message(
                msg_id,
                code,
                message,
                translation_key=translation_key,
                translation_domain=translation_domain,
                translation_placeholders=translation_placeholders,
            )
        )

    def context(self, msg: dict[str, Any]) -> Context:
        """Return a basic Home Assistant Context for use in tests."""
        _ = msg
        return Context()

    def async_handle_exception(self, msg: dict[str, Any], err: Exception) -> None:
        """Record an exception so tests can inspect it."""
        _ = msg
        self.sent = {"_exception": str(err)}

    def async_handle_close(self) -> None:
        """Clean up subscriptions similar to a real connection closing."""
        for unsub in list(self.subscriptions.values()):
            with contextlib.suppress(Exception):
                unsub()
        self.subscriptions.clear()

    def set_supported_features(self, features: dict[str, float]) -> None:
        """Set supported features and update coalescing flag."""
        self.supported_features = features
        self.can_coalesce = features.get("coalesce", False)

    def get_description(self, request: Any | None = None) -> str:
        """Return a basic description of the connection.

        Optionally includes the request in the string.
        """
        name = getattr(self.user, "name", "")
        if request:
            return f"{name} {request}"
        return name


def create_device_with_entity(
    hass: Any,
    device_id: str,
    entity_domain: str = "sensor",
    entity_unique_id: str | None = None,
) -> tuple[MockConfigEntry, DeviceEntry, RegistryEntry]:
    """Create a device linked to a config entry and an entity for tests.

    Returns a tuple: (config_entry, device_entry, entity_entry).

    - `device_id` is used as the underlying Node-RED device identifier.
    - `entity_domain` and `entity_unique_id` determine the created entity; if
      `entity_unique_id` is None it will default to the device_id.
    """
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
    )

    ent_reg = er.async_get(hass)
    unique_id = entity_unique_id or device_id
    entity = ent_reg.async_get_or_create(
        entity_domain, DOMAIN, unique_id, device_id=device.id
    )

    return entry, device, entity
