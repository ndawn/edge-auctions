from base64 import b64encode
from hashlib import md5
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlencode

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from auctions.config import Config
from auctions.dependencies import injectable


@injectable
class PasswordService:
    def __init__(self, password_hasher: PasswordHasher, config: Config) -> None:
        self.hasher = password_hasher
        self.config = config

    def check_password(self, password: str, hashed_password: str) -> bool:
        try:
            return self.hasher.verify(hashed_password, password)
        except VerifyMismatchError:
            return False

    def generate_shop_password(self, token: str) -> str:
        sequence = (self.config.shop_secret + token).encode("utf-8")
        return md5(sequence).hexdigest()

    def hash_password(self, password: str) -> str:
        return self.hasher.hash(password)

    @staticmethod
    def verify_vk_signature(query: dict[str, ...], client_secret: str) -> bool:
        if not query.get("sign"):
            return False

        vk_subset = sorted(filter(lambda key: key.startswith("vk_"), query))

        if not vk_subset:
            return False

        ordered = {k: query[k] for k in vk_subset}

        hash_code = b64encode(
            HMAC(
                client_secret.encode(),
                urlencode(ordered, doseq=True).encode(),
                sha256,
            ).digest()
        ).decode("utf-8")

        if hash_code[-1] == "=":
            hash_code = hash_code[:-1]

        hash_code = hash_code.replace("+", "-").replace("/", "_")
        return query.get("sign") == hash_code
