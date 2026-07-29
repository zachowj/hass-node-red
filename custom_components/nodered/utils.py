"""Helpers for node-red."""

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder

from .const import CONF_CONTRIB_VERSION, DOMAIN


def contrib_announced_version(hass: HomeAssistant) -> bool:
    """Return True when contrib has stored a package version on the config entry."""
    return any(
        entry.data.get(CONF_CONTRIB_VERSION)
        for entry in hass.config_entries.async_entries(DOMAIN)
    )


class NodeRedJSONEncoder(JSONEncoder):
    """JSONEncoder that supports timedelta objects and falls back to the Home Assistant Encoder."""

    def default(self, o: Any) -> Any:
        """Convert timedelta objects.

        Hand other objects to the Home Assistant JSONEncoder.
        """
        if isinstance(o, timedelta):
            return o.total_seconds()

        return JSONEncoder.default(self, o)
