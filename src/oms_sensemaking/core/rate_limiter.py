import logging
import threading
import time
from functools import wraps

LOGGER: logging.Logger = logging.getLogger(__name__)

_rate_limit_lock = threading.Lock()


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
        limiter = rate_decorator_factory(calls, period)
        for cls_attribute_name, cls_attribute_value in cls.__dict__.items():
            if cls_attribute_name.startswith("__"):
                continue
            if callable(cls_attribute_value):
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

    state = {
        "window_start": time.time(),
        "count": 0,
    }

    def rate_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            with _rate_limit_lock:
                max_calls = calls() if callable(calls) else calls
                window = period() if callable(period) else period
                now = time.time()

                # reset window if expired
                if now - state["window_start"] >= window:
                    state["window_start"] = now
                    state["count"] = 0

                if state["count"] >= max_calls:
                    sleep_time = window - (now - state["window_start"])
                    if sleep_time > 0:
                        LOGGER.info(
                            "Rate limit hit. Sleeping for %.2f seconds and retrying",
                            sleep_time,
                        )
                        time.sleep(sleep_time)
                        state["window_start"] = time.time()
                        state["count"] = 0

                state["count"] += 1

            return function(*args, **kwargs)

        return wrapper

    return rate_decorator
