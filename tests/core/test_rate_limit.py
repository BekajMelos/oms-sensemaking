import time

from oms_sensemaking.core.rate_limiter import rate_limiter


@rate_limiter(calls=5, period=5)
class MyLimitedClass:
    def foo(self):
        return "foo"

    def bar(self):
        return "bar"


def test_rate_limiting_works():
    obj = MyLimitedClass()
    for _ in range(4):
        assert obj.foo() == "foo"

    for _ in range(1):
        assert obj.bar() == "bar"

    start = time.time()
    assert obj.bar() == "bar"
    end = time.time()

    assert end - start >= 5
