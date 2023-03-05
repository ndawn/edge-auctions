from functools import wraps

from flask import request
from werkzeug.exceptions import HTTPException

from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.exceptions import ForbiddenError
from auctions.exceptions import UserNotAuthenticatedError
from auctions.services.users_service import UsersService
from auctions.utils.resource_protector import require_auth
from auctions.utils.response import JsonResponse


def extract_token(in_query: bool) -> str:
    if in_query:
        return request.args.get("token", "")
    else:
        return request.headers.get("Authorization", "").split()[-1]


def login_required(*, is_admin: bool = True, inject_user: bool = False) -> callable:
    def decorator(func: callable) -> callable:
        @wraps(func)
        @inject
        def decorated(*args, users_service: UsersService = Provide(), **kwargs) -> JsonResponse:
            try:
                with require_auth.acquire() as token:
                    user = users_service.get_user_by_token(token)
            except HTTPException as exception:
                if exception.code == 401:
                    raise UserNotAuthenticatedError() from exception

                raise

            if user is None:
                raise UserNotAuthenticatedError()

            if user.is_banned:
                raise ForbiddenError()

            if not user.is_admin and is_admin:
                raise ForbiddenError()

            if inject_user:
                return func(user=user, *args, **kwargs)

            return func(*args, **kwargs)

        return decorated

    return decorator
