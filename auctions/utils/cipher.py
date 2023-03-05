import base64
from typing import AnyStr

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key: bytes) -> None:
        self.key = key

    def encrypt(self, raw: str) -> str:
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode("utf-8")

    def decrypt(self, ciphertext: str):
        ciphertext_bytes = base64.b64decode(ciphertext.encode("utf-8"))
        iv = ciphertext_bytes[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(ciphertext_bytes[AES.block_size:])).decode("utf-8")

    @staticmethod
    def _pad(data: AnyStr) -> AnyStr:
        return data + (AES.block_size - len(data) % AES.block_size) * chr(AES.block_size - len(data) % AES.block_size)

    @staticmethod
    def _unpad(data: AnyStr) -> AnyStr:
        return data[:-ord(data[len(data) - 1:])]
