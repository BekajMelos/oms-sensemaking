import logging
import threading
import time
from functools import wraps
from typing import Any

from ratelimit import RateLimitException, limits

LOGGER: logging.Logger = logging.getLogger(__name__)

_rate_limit_lock = threading.Lock()
# Store original methods before rate limiting for hot reload
_rate_limited_classes: dict[type, dict[str, Any]] = {}


def rate_limiter(calls, period):
    """
    A function used to create a class decorator which
    limits API calls and is used on whole classes

    :param calls: The maximum amount of calls across each method in the class
    :param period: The time period for which the maximum calls can be reached
    :return: 'class_decorator' which is a helper method used to create the decorator
    that is used on a given class
    """

    def class_decorator(cls):
        # Store original methods for hot reload
        if cls not in _rate_limited_classes:
            _rate_limited_classes[cls] = {}

        limiter = rate_decorator_factory(calls, period)
        for cls_attribute_name, cls_attribute_value in cls.__dict__.items():
            if cls_attribute_name.startswith("__"):
                continue
            if callable(cls_attribute_value):
                # Store original method if not already stored
                if cls_attribute_name not in _rate_limited_classes[cls]:
                    # Get the original unwrapped method
                    original = getattr(cls_attribute_value, "__wrapped__", cls_attribute_value)
                    _rate_limited_classes[cls][cls_attribute_name] = original
                wrapped = limiter(cls_attribute_value)
                setattr(cls, cls_attribute_name, wrapped)
        return cls

    return class_decorator


def rate_decorator_factory(calls, period):
    """
    A function used to create a rate decorator applied mass to a class' instance methods

    :param calls: The maximum amount of calls each method is collectively is limited to
    :param period: The time period for which the maximum calls can be reached
    :return: Return a rate decorator
    """

    @sleep_and_retry_with_logs
    @limits(calls=calls, period=period)
    def token_bucket():
        return True

    def rate_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            with _rate_limit_lock:
                token_bucket()
            return function(*args, **kwargs)

        return wrapper

    return rate_decorator


def sleep_and_retry_with_logs(func):
    """
    (A rewrite of the @sleep_and_retry decorator from the ratelimit library which adds logging)

    Return a wrapped function that rescues rate limit exceptions, sleeping the
    current thread until rate limit resets.

    :param function func: The function to decorate.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kargs):
        while True:
            try:
                return func(*args, **kargs)
            except RateLimitException as exception:
                sleep_time = exception.period_remaining
                LOGGER.info("Rate limit hit. Sleeping for %.2f seconds and retrying", sleep_time)
                time.sleep(sleep_time)

    return wrapper


def update_rate_limiter_for_class(cls, calls, period):
    """
    Update rate limiter settings for a class that was previously rate limited.
    This allows hot-reloading of rate limit settings without restarting.

    :param cls: The class to update
    :param calls: New maximum amount of calls
    :param period: New time period
    """
    if cls not in _rate_limited_classes:
        LOGGER.warning("Class %s was not previously rate limited, cannot update", cls.__name__)
        return

    limiter = rate_decorator_factory(calls, period)
    original_methods = _rate_limited_classes[cls]

    for method_name, original_method in original_methods.items():
        wrapped = limiter(original_method)
        setattr(cls, method_name, wrapped)

    LOGGER.info("Updated rate limiter for %s: %d calls per %d seconds", cls.__name__, calls, period)
