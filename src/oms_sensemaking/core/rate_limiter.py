from functools import wraps

from ratelimit import limits

from oms_sensemaking.config import SETTINGS


def rate_limit_methods(rate_decorator):
    def class_decorator(cls):
        for cls_attribute_name, cls_attribute_value in cls.__dict__.items():
            if cls_attribute_name.startswith("__"):
                continue
            if callable(cls_attribute_value):
                wrapped = rate_decorator(cls_attribute_value)
                setattr(cls, cls_attribute_name, wrapped)
        return cls

    return class_decorator


def rate_decorator(function):
    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    @wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper
