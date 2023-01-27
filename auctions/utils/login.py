from functools import wraps

from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.exceptions import ForbiddenError
from auctions.exceptions import UserNotAuthenticatedError
from auctions.services.users_service import UsersService
from auctions.utils.resource_protector import require_auth
from auctions.utils.response import JsonResponse


def login_required(*, is_admin: bool = True, inject_user: bool = False) -> callable:
    def decorator(func: callable) -> callable:
        @wraps(func)
        @inject
        def decorated(*args, users_service: UsersService = Provide(), **kwargs) -> JsonResponse:
            with require_auth.acquire() as token:
                user = users_service.get_user(token.sub)

            if user is None:
                raise UserNotAuthenticatedError()

            if not user.is_admin and is_admin:
                raise ForbiddenError()

            if inject_user:
                return func(user=user, *args, **kwargs)

            return func(*args, **kwargs)

        return decorated

    return decorator
