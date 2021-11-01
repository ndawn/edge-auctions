import secrets

from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from auctions.accounts.models import BearerAuthToken, PyUserIn, PyUserOut, User


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
