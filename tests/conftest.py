"""Global fixtures for nodered integration."""

# Fixtures allow you to replace functions with a Mock object. You can perform
# many options via the Mock to reflect a particular behavior from the original
# function that you want to see without going through the function's actual logic.
# Fixtures can either be passed into tests as parameters, or if autouse=True, they
# will automatically be used across all tests.
#
# Fixtures that are defined in conftest.py are available across all tests. You can also
# define fixtures within a particular test file to scope them locally.
#
# pytest_homeassistant_custom_component provides some fixtures that are provided by
# Home Assistant core. You can find those fixture definitions here:
# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/blob/master/pytest_homeassistant_custom_component/common.py
#
# See here for more info: https://docs.pytest.org/en/latest/fixture.html (note that
# pytest includes fixtures OOB which you can use as defined on this page)
from collections.abc import Iterator
import contextlib
from typing import Any
from unittest.mock import patch

import pytest

from tests.helpers import FakeConnection


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    """Enable custom integrations."""
    _ = enable_custom_integrations


# This fixture is used to prevent HomeAssistant from attempting to create and
# dismiss persistent notifications. These calls would fail without this fixture
# since the persistent_notification integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture() -> Iterator[None]:
    """Skip notification calls."""
    with (
        patch("homeassistant.components.persistent_notification.async_create"),
        patch("homeassistant.components.persistent_notification.async_dismiss"),
    ):
        yield


# Pytest fixture that provides a FakeConnection for tests.

# Returns a FakeConnection instance that simulates a real connection so tests
# can exercise connection-dependent logic without relying on external resources.
# Use by declaring the fixture name (``fake_connection``) as a test parameter.


# Returns:
#     FakeConnection: A mock/simulated connection object. The fixture yields a
#     `FakeConnection` instance and ensures it is cleaned up (reset/closed) after
#     the test completes.
@pytest.fixture
def fake_connection() -> Iterator[FakeConnection]:
    conn = FakeConnection()
    try:
        yield conn
    finally:
        # Ensure tests do not leak connection state between tests
        with contextlib.suppress(Exception):
            conn.reset()
        with contextlib.suppress(Exception):
            conn.close()
