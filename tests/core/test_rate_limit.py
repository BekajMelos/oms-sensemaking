import pytest
from ratelimit import RateLimitException

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.rate_limiter import rate_decorator, rate_limit_methods


@rate_limit_methods(rate_decorator)
class MyLimitedClass:
    def foo(self):
        return "foo"

    def bar(self):
        return "bar"


def test_rate_limiting_works():
    obj = MyLimitedClass()
    for _ in range(SETTINGS.maximum_oms_api_calls):
        assert obj.foo() == "foo"

    with pytest.raises(RateLimitException):
        obj.foo()

    for _ in range(SETTINGS.maximum_oms_api_calls):
        assert obj.bar() == "bar"

    with pytest.raises(RateLimitException):
        obj.bar()
