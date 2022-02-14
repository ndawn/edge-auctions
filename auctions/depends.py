from typing import Optional

from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from auctions.accounts.models import BearerAuthToken, PyUser
from auctions.accounts.oauth2 import oauth2_auth_exception, oauth2_scheme
from auctions.supply.models import PySupplySessionUploadStatus


async def get_current_user(token: str = Depends(oauth2_scheme)) -> PyUser:
    token = await BearerAuthToken.get_or_none(token=token).select_related('user')

    if token is None:
        raise oauth2_auth_exception

    return PyUser.from_orm(token.user)


async def get_current_active_user(user: PyUser = Depends(get_current_user)) -> PyUser:
    if not user.is_active:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Current user is not active')

    return user


async def get_current_active_admin(user: PyUser = Depends(get_current_user)) -> PyUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail='Current user does not have permissions to perform the operation',
        )

    return user


class SupplySessionUploadStatusTracker:
    _instance = None
    _sessions: dict[str, PySupplySessionUploadStatus] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __call__(self):
        return self

    def __contains__(self, id_: str) -> bool:
        return id_ in self._sessions

    def get(self, id_: str) -> Optional[PySupplySessionUploadStatus]:
        return self._sessions.get(id_)

    def set(self, id_: str, value: PySupplySessionUploadStatus):
        self._sessions[id_] = value

    def pop(self, id_: str) -> PySupplySessionUploadStatus:
        return self._sessions.pop(id_)
