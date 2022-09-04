from functools import wraps
from typing import Callable

from auctions.db.models.enum import ExternalTokenType


def use_token(token_type: ExternalTokenType) -> Callable:
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs, token_type=token_type)

        return wrapper

    return decorator
