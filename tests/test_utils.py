"""Test helpers."""

from datetime import timedelta

import pytest

from custom_components.nodered.utils import NodeRedJSONEncoder


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
