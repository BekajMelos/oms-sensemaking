"""Tests for PubSub."""

from oms_sensemaking.core.pubsub import PubSub


def test_pubsub():
    pubsub: PubSub = PubSub()
    test_val: bool = False

    def dummy_subscriber():
        nonlocal test_val

        test_val = True

    def dummy_subscriber2(data: dict):
        assert isinstance(data, dict)
        dummy_subscriber()

    pubsub.subscribe("test-event", dummy_subscriber)
    pubsub.subscribe("test-event-with-data", dummy_subscriber2)
    pubsub.publish("test-event")
    pubsub.publish("test-event-with-data", {"msg", "Look Ma! Data"})

    # ensure dispatcher thread is actually running
    assert pubsub.is_running

    # stop thread so this test will exit ;)
    pubsub.stop()

    # ensure dispatcher thread is no longer running
    assert not pubsub.is_running

    # ensure subscriber ran
    assert test_val

    # ensure unsubscribing worked
    assert pubsub.unsubscribe("test-event", dummy_subscriber)

    # ensure unsubscribing a non-existent subscriber is non-fatal
    assert not pubsub.unsubscribe("test-event", dummy_subscriber)

    # ensure unsubscribing to a non-existent event is non-fatal
    assert not pubsub.unsubscribe("foo-event", dummy_subscriber)
