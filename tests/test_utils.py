"""Test helpers."""

from datetime import timedelta
import json
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nodered.const import CONF_CONTRIB_VERSION, DOMAIN, VERSION
from custom_components.nodered.utils import (
    NodeRedJSONEncoder,
    contrib_announced_version,
    contrib_supports_presence_available,
)
from custom_components.nodered.version import __version__
from homeassistant.core import HomeAssistant


def test_version_matches_manifest() -> None:
    """VERSION is loaded from manifest.json (release-please source of truth)."""
    manifest = json.loads(
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("custom_components/nodered/manifest.json")
        .read_text(encoding="utf-8")
    )
    assert VERSION == __version__ == manifest["version"]


def test_contrib_announced_version_from_entry_data(hass: HomeAssistant) -> None:
    """Helper is true when contrib_version is stored on the entry."""
    assert contrib_announced_version(hass) is False

    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert contrib_announced_version(hass) is False

    hass.config_entries.async_update_entry(entry, data={CONF_CONTRIB_VERSION: "0.80.3"})
    assert contrib_announced_version(hass) is True


def test_contrib_supports_presence_available_aliases_announced(
    hass: HomeAssistant,
) -> None:
    """Presence-available capability tracks announced version."""
    assert contrib_supports_presence_available(hass) is False
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_CONTRIB_VERSION: "0.80.3"})
    entry.add_to_hass(hass)
    assert contrib_supports_presence_available(hass) is True
    assert contrib_supports_presence_available(hass) is contrib_announced_version(hass)


def test_json_encoder() -> None:
    """Test the NodeRedJSONEncoder."""
    ha_json_enc = NodeRedJSONEncoder()

    # Test serializing a timedelta
    data = timedelta(
        days=1,
        hours=2,
        minutes=3,
    )
    assert ha_json_enc.default(data) == data.total_seconds()


def test_json_encoder_serializes_via_json_dumps() -> None:
    # Lazy import to avoid adding new module-level imports in this file.
    import json  # noqa: PLC0415

    payload = {"duration": timedelta(hours=1, minutes=30)}
    dumped = json.dumps(payload, cls=NodeRedJSONEncoder)
    loaded = json.loads(dumped)
    assert loaded["duration"] == payload["duration"].total_seconds()


def test_json_encoder_preserves_fractional_seconds() -> None:
    td = timedelta(seconds=1, microseconds=500000)  # 1.5 seconds
    enc = NodeRedJSONEncoder()
    assert enc.default(td) == td.total_seconds()


def test_json_encoder_delegates_and_raises_for_unknown_types() -> None:
    class Unknown:
        pass

    enc = NodeRedJSONEncoder()
    try:
        enc.default(Unknown())  # type: ignore[arg-type]
    except TypeError:
        # Expected: JSONEncoder.default raises TypeError for unknown objects
        return
    pytest.fail("Expected TypeError when encoding an unsupported object type")
