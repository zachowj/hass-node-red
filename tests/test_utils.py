"""Test helpers."""

from datetime import datetime, timedelta

from custom_components.nodered.utils import NodeRedJSONEncoder, convert_iso_to_datetime


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


def test_json_encoder_fallback_raises_on_unknown_type(hass):
    """The encoder should delegate unknown types to the base JSONEncoder (which raises)."""
    ha_json_enc = NodeRedJSONEncoder()

    class Dummy:
        pass

    try:
        ha_json_enc.default(Dummy())
        assert False, "Expected TypeError for unknown type"
    except TypeError:
        pass


def test_convert_iso_to_datetime_valid_iso(hass):
    dt = convert_iso_to_datetime("2021-04-05T12:34:56Z")
    assert isinstance(dt, datetime)
    assert dt.year == 2021 and dt.month == 4 and dt.day == 5
    assert dt.hour == 12 and dt.minute == 34 and dt.second == 56
    assert dt.tzinfo is not None


def test_convert_iso_to_datetime_date_only(hass):
    dt = convert_iso_to_datetime("2021-04-05")
    assert isinstance(dt, datetime)
    assert dt.year == 2021 and dt.month == 4 and dt.day == 5
    assert dt.hour == 0 and dt.minute == 0 and dt.second == 0
    assert dt.tzinfo is None


def test_convert_iso_to_datetime_invalid_string_returns_none(hass):
    assert convert_iso_to_datetime("not-a-date") is None


def test_convert_iso_to_datetime_none_returns_none(hass):
    assert convert_iso_to_datetime(None) is None
