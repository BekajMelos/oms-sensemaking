import logging
import time
from functools import wraps

from ratelimit import RateLimitException, limits

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


def low_frequency(function):
    """
    A function used as a decorator to set the rate multiplier of a method
    within a class (low)

    :param function: The function which this rate will be applied to
    :return: The rate modified function
    """
    function.rate_multiplier = SETTINGS.low_frequency_multiplier
    return function


def medium_frequency(function):
    """
    A function used as a decorator to set the rate multiplier of a method
    within a class (medium)

    :param function: The function which this rate will be applied to
    :return: The rate modified function
    """
    function.rate_multiplier = SETTINGS.medium_frequency_multiplier
    return function


def high_frequency(function):
    """
    A function used as a decorator to set the rate multiplier of a method
    within a class (high)

    :param function: The function which this rate will be applied to
    :return: The rate modified function
    """
    function.rate_multiplier = SETTINGS.high_frequency_multiplier
    return function


def rate_limit_methods(calls, period):
    """
    A function used to create a class decorator which
    limits API calls and is used on whole classes

    :param calls: The maximum amount of calls each method in the class is limited to
    :param period: The time period for which the maximum calls can be reached
    :return: 'class_decorator' which is a helper method used to create the decorator
    that is used on a given class
    """
    decorator_cache = {}

    def class_decorator(cls):
        for cls_attribute_name, cls_attribute_value in cls.__dict__.items():
            if cls_attribute_name.startswith("__"):
                continue
            if callable(cls_attribute_value):
                multiplier = getattr(cls_attribute_value, "rate_multiplier", 1)
                effective_calls = calls * multiplier
                if effective_calls not in decorator_cache:
                    decorator_cache[effective_calls] = rate_decorator_factory(effective_calls, period)
                rate_decorator = decorator_cache[effective_calls]
                wrapped = rate_decorator(cls_attribute_value)
                setattr(cls, cls_attribute_name, wrapped)
        return cls

    return class_decorator


def rate_decorator_factory(calls, period):
    """
    A function used to create a rate decorator applied mass to a class' instance methods

    :param calls: The maximum amount of calls the method is limited to
    :param period: The time period for which the maximum calls can be reached
    :return: Return a rate decorator
    """

    def rate_decorator(function):
        """
        A function used to return a method wrapped with a given call limit and call period

        :param function: The function that is to be wrapped
        :return: 'wrapper' which is a helper method used to aggregate the function's specific
        arguments and call it
        """

        @sleep_and_retry_with_logs
        @limits(calls=calls, period=period)
        @wraps(function)
        def wrapper(*args, **kwargs):
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
                LOGGER.info(f"Rate limit hit for {func}. Sleeping for {sleep_time:.2f} seconds and retrying")
                time.sleep(sleep_time)

    return wrapper
