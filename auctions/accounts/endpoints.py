import secrets

from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from auctions.accounts.models import BearerAuthToken, PyUser, PyUserIn, PyUserOut, User
from auctions.depends import get_current_user


router = APIRouter(redirect_slashes=False)


DEFAULT_TAG = 'Accounts'


@router.post('/login', tags=[DEFAULT_TAG], response_model=PyUserOut)
async def authorize_user(data: PyUserIn) -> PyUserOut:
    user = await User.get_user(email=data.username, password=data.password)

    if user is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='User with specified email does not exist or password is incorrect',
        )

    token = await BearerAuthToken.create(user=user, token=secrets.token_urlsafe(48))

    py_user = PyUserOut.from_orm(user)
    py_user.access_token = token.token
    return py_user


@router.get('/me', tags=[DEFAULT_TAG], response_model=PyUserOut, response_model_exclude={'access_token'})
async def get_me(user: PyUser = Depends(get_current_user)) -> PyUserOut:
    return PyUserOut(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )
