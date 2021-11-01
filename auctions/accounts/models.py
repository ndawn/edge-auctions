import secrets
from typing import Optional

from pydantic import BaseModel
from tortoise import fields

from auctions.accounts.passwords import check_password, hash_password
from auctions.utils.abstract_models import CreatedRecordedModel, CreatedUpdatedRecordedModel


class User(CreatedUpdatedRecordedModel):
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    is_admin = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)

    @classmethod
    async def create_user(
        cls,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        is_admin: bool = False,
        is_active: bool = True,
    ) -> "User":
        password_hash = hash_password(password)

        return await cls.create(
            email=email,
            password=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            is_active=is_active,
        )

    @classmethod
    async def get_user(cls, email: str, password: str) -> Optional["User"]:
        user = await cls.get_or_none(email=email)

        if user is None:
            return None

        if not check_password(password, user.password):
            return None

        return user


class BearerAuthToken(CreatedRecordedModel):
    user = fields.ForeignKeyField('accounts.User', on_delete=fields.CASCADE)
    token = fields.CharField(max_length=64)

    @classmethod
    async def create_token(cls, user: User) -> "BearerAuthToken":
        return await cls.create(
            user=user,
            token=secrets.token_urlsafe(48),
        )

    @classmethod
    async def get_token(cls, token: str) -> Optional["BearerAuthToken"]:
        return await cls.get_or_none(token=token).select_related('user')


class PyUserIn(BaseModel):
    username: str
    password: str


class PyUserOut(BaseModel):
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_active: bool
    access_token: Optional[str]

    class Config:
        orm_mode = True


class PyUser(PyUserOut):
    password: str

    class Config:
        orm_mode = True


class PyBearerAuthToken(BaseModel):
    user: PyUser
    token: str

    class Config:
        orm_mode = True
