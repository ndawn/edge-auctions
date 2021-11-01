from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_401_UNAUTHORIZED


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/accounts/login')

oauth2_auth_exception = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail='Invalid authorization credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)
