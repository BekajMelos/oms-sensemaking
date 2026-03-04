"""Buffer Unit Tests"""

import threading
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from oms_sensemaking.core.buffer import Buffer

# class TestController(SensemakerController):

#     # def __init__(self):
#     #     pass

#     def process_buffer(list_id, object_list):
#         return True


def test_callback_func():
    return True


@pytest.fixture
def mock_buffer():
    buffer = Buffer("test buffer", 10, test_callback_func)

    # disable autoflush so that flush_buffer doesn't go on forever. Without this the tests never end
    buffer.autoflush_enabled = False
    return buffer


# TODO remove this is a duplicate really
# def test_process_track_too_short_triggers_cleanup(mocker, mock_buffer):
#     track_uuid = uuid4()
#     mock_geo_controller._track_generator.generate_track = mocker.Mock(side_effect=TrackLengthError)

#     # populate shared dicts
#     mock_geo_controller.track_times[track_uuid] = datetime.now(tz=timezone.utc)
#     mock_geo_controller.track_node_buffer[track_uuid] = []
#     mock_geo_controller.node_track_mapping[uuid4()] = track_uuid

#     result = mock_geo_controller._process_track(track_uuid)

#     assert result is False
#     assert track_uuid in mock_geo_controller.track_times
#     assert mock_geo_controller.track_times[track_uuid] is None


def test__execute_callback_and_expire_handles_errors(mocker, mock_buffer: Buffer):
    list_id = uuid4()
    mock_buffer.callback_func = mocker.Mock(side_effect=RuntimeError("fail"))

    mock_buffer.expiration_times[list_id] = datetime.now(tz=timezone.utc)
    mock_buffer.object_list_buffer[list_id] = []
    mock_buffer.id_mapping[uuid4()] = list_id

    result = mock_buffer._execute_callback_and_expire(list_id, [])
    assert not result
    assert list_id in mock_buffer.expiration_times
    assert mock_buffer.expiration_times[list_id] is None


def test_concurrent_flush_buffer_thread_safety(mock_buffer):
    # prepare buffer with several tracks
    for _ in range(10):
        list_id = uuid4()
        mock_buffer.expiration_times[list_id] = datetime.now(tz=timezone.utc) - timedelta(seconds=999)
        mock_buffer.object_list_buffer[list_id] = []

    threads = [threading.Thread(target=mock_buffer._flush_buffer) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All expired tracks should be processed & cleaned
    assert all(v is None for v in mock_buffer.expiration_times.values())


def test_lock_is_used_during_flush_buffer(mock_buffer):
    class SpyLock:
        def __init__(self, real_lock):
            self.real_lock = real_lock
            self.enter_called = False

        def __enter__(self):
            self.enter_called = True
            return self.real_lock.__enter__()

        def __exit__(self, *args):
            return self.real_lock.__exit__(*args)

    spy_lock = SpyLock(threading.Lock())
    mock_buffer.lock = spy_lock

    mock_buffer._flush_buffer()

    assert spy_lock.enter_called, "Expected _flush_buffer() to use the lock"
