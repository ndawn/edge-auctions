from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN


from auctions.accounts.models import BearerAuthToken, PyUser
from auctions.accounts.oauth2 import oauth2_auth_exception, oauth2_scheme


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
