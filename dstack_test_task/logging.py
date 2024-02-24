import functools
import logging
from typing import Callable


def catch(logger: logging.Logger = logging.getLogger(__name__)):
    def decorator(function: Callable):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as exc:
                logger.error(f"Error: {exc}")

        return wrapper
    return decorator
