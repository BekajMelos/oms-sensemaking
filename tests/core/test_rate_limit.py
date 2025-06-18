import time

from oms_sensemaking.core.rate_limiter import rate_limit_methods


@rate_limit_methods(calls=2, period=2)
class MyLimitedClass:
    def foo(self):
        return "foo"

    def bar(self):
        return "bar"


def test_rate_limiting_works():
    obj = MyLimitedClass()
    for _ in range(2):
        assert obj.foo() == "foo"

    start = time.time()
    assert obj.foo() == "foo"
    end = time.time()

    assert end - start >= 1

    for _ in range(2):
        assert obj.bar() == "bar"

    start = time.time()
    assert obj.bar() == "bar"
    end = time.time()

    assert end - start >= 1
