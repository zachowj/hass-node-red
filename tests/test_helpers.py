"""Tests for helpers.py."""

from homeassistant.components.websocket_api.messages import (
    error_message,
    event_message,
    result_message,
)
from homeassistant.core import Context
from tests.helpers import FakeConnection


def test_fake_connection__async_handle_close_clears_subscriptions_and_calls_unsubs(
    fake_connection: FakeConnection,
) -> None:
    called: dict[str, bool] = {"a": False, "b": False}

    def unsub_a() -> None:
        called["a"] = True

    def unsub_b() -> None:
        called["b"] = True
        msg = "boom"
        raise RuntimeError(msg)

    fake_connection.subscriptions["a"] = unsub_a
    fake_connection.subscriptions["b"] = unsub_b

    # Should call both and clear the subscriptions without raising
    fake_connection.async_handle_close()

    assert called["a"] is True
    assert called["b"] is True
    assert fake_connection.subscriptions == {}


def test_fake_connection__context_and_description_and_features(
    fake_connection: FakeConnection,
) -> None:
    ctx = fake_connection.context({"id": 1})
    assert isinstance(ctx, Context)

    # description without request
    assert isinstance(fake_connection.get_description(), str)
    # description with request
    assert "req" in fake_connection.get_description("req")

    # set supported features controls coalescing
    fake_connection.set_supported_features({"coalesce": True})
    assert fake_connection.can_coalesce is True


def test_async_handle_exception_records_exception(
    fake_connection: FakeConnection,
) -> None:
    fake_connection.async_handle_exception({"id": 1}, RuntimeError("fail"))
    assert fake_connection.sent_history[-1] == {"_exception": "fail"}


def test_fake_connection_send_wrappers(fake_connection: FakeConnection) -> None:
    # Send a sequence of messages and assert history records them in order
    before = len(fake_connection.sent_history)

    fake_connection.send_message({"a": 1})
    assert len(fake_connection.sent_history) == before + 1
    assert fake_connection.sent_history[-1] == {"a": 1}

    fake_connection.send_result(5, {"ok": True})
    assert fake_connection.sent_history[-1] == result_message(5, {"ok": True})

    fake_connection.send_event(7, {"ev": 1})
    assert fake_connection.sent_history[-1] == event_message(7, {"ev": 1})

    fake_connection.send_error(8, "code", "msg")
    assert fake_connection.sent_history[-1] == error_message(8, "code", "msg")


def test_fake_connection_deepcopy_of_messages(fake_connection: FakeConnection) -> None:
    # Ensure messages are deep-copied when stored in history
    mutable = {"a": {"inner": 1}}
    fake_connection.send_message(mutable)
    # Mutate original
    mutable["a"]["inner"] = 2
    assert fake_connection.sent_history[-1]["a"]["inner"] == 1


def test_fake_connection_reset_clears_history_and_subscriptions(
    fake_connection: FakeConnection,
) -> None:
    # Send a message and register a subscription, then reset
    fake_connection.send_message({"x": 1})
    called = {"unsub_called": False}

    def unsub():
        called["unsub_called"] = True

    fake_connection.register_subscription("m1", unsub)

    # Reset should clear history and subscriptions
    fake_connection.reset()
    assert fake_connection.sent is None
    assert fake_connection.sent_history == []
    assert fake_connection.subscriptions == {}


def test_fake_connection_close_calls_subscriptions_and_clears(
    fake_connection: FakeConnection,
) -> None:
    called: dict[str, bool] = {"a": False, "b": False}

    def unsub_a() -> None:
        called["a"] = True

    def unsub_b() -> None:
        called["b"] = True
        raise RuntimeError("boom")

    fake_connection.register_subscription("a", unsub_a)
    fake_connection.register_subscription("b", unsub_b)

    # close() is an alias to async_handle_close(); both should call unsub functions
    fake_connection.close()

    assert called["a"] is True
    assert called["b"] is True
    assert fake_connection.subscriptions == {}
