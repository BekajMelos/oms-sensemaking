from unittest import mock

from oms_sensemaking.core.rate_limiter import rate_limiter


def test_rate_limiter_counts_across_methods():
    @rate_limiter(calls=3, period=10)
    class C:
        def a(self):
            return "a"

        def b(self):
            return "b"

    obj = C()

    with mock.patch("time.sleep") as mock_sleep:
        obj.a()
        obj.b()
        obj.a()  # 3rd call, limit reached
        obj.b()  # 4th call, should trigger sleep

        mock_sleep.assert_called_once()


def test_rate_limiter_resets_after_window():
    @rate_limiter(calls=2, period=5)
    class C:
        def x(self):
            return "x"

    obj = C()

    fake_time = [100.0]  # mutable so we can advance it

    def time_side_effect():
        return fake_time[0]

    with mock.patch("time.time", side_effect=time_side_effect), mock.patch("time.sleep") as mock_sleep:
        obj.x()  # call 1
        obj.x()  # call 2

        # Still in window, should sleep
        obj.x()
        mock_sleep.assert_called_once()

        # Advance time past window
        fake_time[0] += 6

        # Should not sleep again — window reset
        obj.x()
        assert mock_sleep.call_count == 1
