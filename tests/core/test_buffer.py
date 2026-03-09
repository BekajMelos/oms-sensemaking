"""Buffer Unit Tests"""

import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from oms_sensemaking.core.buffer import Buffer
from oms_sensemaking.core.exceptions import TrackLengthError


def test_callback_func():
    """Empty callback func"""
    return True


class TestBuffer:
    """Test callback function"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup the buffer"""
        self.buffer = Buffer("test buffer", 10)
        self.buffer.callback_func = test_callback_func

        # set this to false so that the tests don't try to run this multiple times
        self.buffer.autoflush_enabled = False
        yield

    def test_add(self):
        """Test that objects added to the buffer update the lists properly"""

        node_id1 = uuid4()
        node_id2 = uuid4()
        obj1 = {"id": 1}
        obj2 = {"id": 2}
        obj3 = {"id": 3}

        self.buffer.add(node_id1, obj1)
        self.buffer.add(node_id1, obj2)
        self.buffer.add(node_id2, obj3)

        assert len(self.buffer.id_mapping.keys()) == 2
        list_id1 = self.buffer.id_mapping[node_id1]
        list_id2 = self.buffer.id_mapping[node_id2]

        assert isinstance(list_id1, UUID)
        assert len(self.buffer.expiration_times.keys()) == 2
        assert isinstance(self.buffer.expiration_times[list_id1], datetime)
        assert len(self.buffer.object_list_buffer.keys()) == 2
        assert self.buffer.object_list_buffer[list_id1] == [obj1, obj2]
        assert self.buffer.object_list_buffer[list_id2] == [obj3]

    def test__get_id_list(self):
        """Test _get_id_list returns the correct uuids"""

        node_id1 = uuid4()
        node_id2 = uuid4()

        # test that same input id gets the same list id
        node_id1_list_id = self.buffer._get_list_id(node_id1)
        node_id1_list_id_again = self.buffer._get_list_id(node_id1)
        assert node_id1_list_id == node_id1_list_id_again

        # different id should get a new list id
        node_id2_list_id = self.buffer._get_list_id(node_id2)
        assert node_id1_list_id != node_id2_list_id

    def test__flush_buffer(self):
        """Test flush buffer only flushes expired tracks"""
        list_id1 = uuid4()
        list1 = [{"id": 1}, {"id": 2}]
        list_id2 = uuid4()
        list2 = [{"id": 3}]
        # add one list that should be expired and one that should not be expired
        self.buffer.expiration_times[list_id1] = datetime.now(tz=timezone.utc) - timedelta(seconds=999)
        self.buffer.expiration_times[list_id2] = datetime.now(tz=timezone.utc) + timedelta(seconds=999)
        self.buffer.object_list_buffer[list_id1] = list1
        self.buffer.object_list_buffer[list_id2] = list2

        self.buffer.callback_func = MagicMock()
        self.buffer._flush_buffer()
        self.buffer.callback_func.assert_called_once_with(list_id1, list1)

    def test__execute_callback_and_expire_handles_errors(self, mocker):
        """Test handling errors in callback"""
        list_id = uuid4()
        self.buffer.callback_func = mocker.Mock(side_effect=TrackLengthError("fail"))

        self.buffer.expiration_times[list_id] = datetime.now(tz=timezone.utc)
        self.buffer.object_list_buffer[list_id] = []
        self.buffer.id_mapping[uuid4()] = list_id

        self.buffer._execute_callback_and_expire(list_id, [])
        assert list_id in self.buffer.expiration_times
        assert self.buffer.expiration_times[list_id] is None

    def test_concurrent_flush_buffer_thread_safety(self):
        """Test that flush_buffer threads clean up properly"""

        # prepare buffer with several tracks
        for _ in range(10):
            list_id = uuid4()
            self.buffer.expiration_times[list_id] = datetime.now(tz=timezone.utc) - timedelta(seconds=999)
            self.buffer.object_list_buffer[list_id] = []

        threads = [threading.Thread(target=self.buffer._flush_buffer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All expired tracks should be processed & cleaned
        assert all(v is None for v in self.buffer.expiration_times.values())

    def test_lock_is_used_during_flush_buffer(self):
        """Test lock is used during flush buffer"""

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
        self.buffer.lock = spy_lock

        self.buffer._flush_buffer()

        assert spy_lock.enter_called, "Expected _flush_buffer() to use the lock"
