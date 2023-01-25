from argon2 import PasswordHasher

from auctions.dependencies import injectable


PasswordHasher = injectable(PasswordHasher)
