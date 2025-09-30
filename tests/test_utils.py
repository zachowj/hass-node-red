"""Test helpers."""

from datetime import timedelta

from custom_components.nodered.utils import NodeRedJSONEncoder


def test_json_encoder(hass):
    """Test the NodeRedJSONEncoder."""
    ha_json_enc = NodeRedJSONEncoder()

    # Test serializing a timedelta
    data = timedelta(
        days=1,
        hours=2,
        minutes=3,
    )
    assert ha_json_enc.default(data) == data.total_seconds()
