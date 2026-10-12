"""Helpers for node-red."""

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder

from .const import CONTRIB_VERSION_DATA


def contrib_announced_version(hass: HomeAssistant) -> bool:
    """Return True when contrib has announced its package version."""
    return bool(hass.data.get(CONTRIB_VERSION_DATA))


def contrib_supports_presence_available(hass: HomeAssistant) -> bool:
    """Whether presence-available entity semantics apply."""
    return contrib_announced_version(hass)


class NodeRedJSONEncoder(JSONEncoder):
    """JSONEncoder that supports timedelta objects and falls back to the Home Assistant Encoder."""

    def default(self, o: Any) -> Any:
        """Convert timedelta objects.

        Hand other objects to the Home Assistant JSONEncoder.
        """
        if isinstance(o, timedelta):
            return o.total_seconds()

        return JSONEncoder.default(self, o)
