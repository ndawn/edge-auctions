from functools import wraps
from typing import Callable

from authlib.integrations.flask_oauth2 import ResourceProtector

from auctions.dependencies import inject
from auctions.exceptions import ForbiddenError
from auctions.exceptions import UserNotAuthenticatedError
from auctions.services.users_service import UsersService
from auctions.utils.response import JsonResponse

require_auth = ResourceProtector()


def login_required(*, scopes: str | None = None, is_admin: bool = True, inject_user: bool = False) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @require_auth(scopes)
        @inject
        def decorated(
            *args,
            users_service: UsersService,
            **kwargs,
        ) -> JsonResponse:
            from flask import request

            user = users_service.get_current_user(request)

            if user is None:
                raise UserNotAuthenticatedError()

            if not user.is_admin and is_admin:
                raise ForbiddenError()

            if inject_user:
                return func(user=user, *args, **kwargs)

            return func(*args, **kwargs)

        return decorated

    return decorator
