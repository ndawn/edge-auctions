from functools import wraps
from typing import cast
from typing import Callable

from flask import current_app
from sqlalchemy.orm.session import Session

from auctions.db.session import SessionManager
from auctions.services.auth_service import AuthService
from auctions.utils.app import Flask


current_app = cast(Flask, current_app)


def endpoint(
    endpoint_spec: Callable,
    protected: bool = True,
    is_admin: bool = True,
    inject_user: bool = False,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @endpoint_spec
        def decorated(*args, **kwargs) -> ...:
            session_qual_name = current_app.provider.get_qual_name(Session)
            session_manager: SessionManager = current_app.provider.provide(SessionManager)

            with session_manager.session:
                if protected:
                    auth_service = current_app.provider.provide(
                        AuthService,
                        {session_qual_name: session_manager.session},
                    )
                    user = auth_service.authorize_request(is_admin)

                    if inject_user:
                        kwargs["user"] = user

                return current_app.provider.inject(func, {session_qual_name: session_manager.session})(*args, **kwargs)

        return decorated

    return decorator
