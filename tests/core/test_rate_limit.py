import time

import pytest

from oms_sensemaking.core.rate_limiter import rate_limiter


@rate_limiter(calls=5, period=5)
class MyLimitedClass:
    def foo(self):
        return "foo"

    def bar(self):
        return "bar"


@pytest.mark.skip(reason="This test is flaky")
def test_rate_limiting_works():
    obj = MyLimitedClass()
    for _ in range(4):
        assert obj.foo() == "foo"

    for _ in range(1):
        assert obj.bar() == "bar"

    start = time.time()
    obj.bar()
    end = time.time()

    # sleep based off time remaining from last call. just checking if sleeping when it should
    assert end - start >= 1
