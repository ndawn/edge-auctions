from typing import Optional

from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol


def scan_barcode(image: Image) -> tuple[Optional[str], Optional[str]]:
    codes = decode(image, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN5, ZBarSymbol.UPCA])

    upca = next(filter(lambda code: code.type == 'UPCA', codes), None)
    ean13 = next(filter(lambda code: code.type == 'EAN13', codes), None)
    ean5 = next(filter(lambda code: code.type == 'EAN5', codes), None)

    if upca is not None:
        upca = upca.data.decode()

    if ean13 is not None:
        ean13 = ean13.data.decode()[1:]

    if ean5 is not None:
        ean5 = ean5.data.decode()

    return upca or ean13, ean5
