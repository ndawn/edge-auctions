import asyncio
from getpass import getpass

from tortoise import Tortoise

from auctions.config import TORTOISE_ORM
from auctions.accounts.models import User
from auctions.accounts.passwords import hash_password


async def create_user():
    await Tortoise.init(TORTOISE_ORM)

    username = input('Enter username: ')

    while True:
        password = getpass('Enter password: ')
        confirm = getpass('Enter password again: ')
        if password == confirm:
            break

    first_name = input('Enter user first name: ')
    last_name = input('Enter user last name: ')

    user = await User.create_user(
        email=username,
        password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )

    return user.pk

if __name__ == '__main__':
    asyncio.run(create_user())
