from argon2.exceptions import VerifyMismatchError
from flask import current_app


class PasswordService:
    def __init__(self):
        self.hasher = current_app.config["PASSWORD_HASHER"]

    def check_password(self, password: str, hashed_password: str) -> bool:
        try:
            return self.hasher.verify(hashed_password, password)
        except VerifyMismatchError:
            return False

    def hash_password(self, password: str) -> str:
        return self.hasher.hash(password)
