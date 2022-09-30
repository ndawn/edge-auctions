import threading
import time
from mimetypes import guess_extension
from mimetypes import guess_type
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pyvips
from flask import current_app
from PIL import Image as PillowImage
from pyzbar.pyzbar import ZBarSymbol
from pyzbar.pyzbar import decode
from werkzeug.formparser import FileStorage

from auctions.config import Config
from auctions.config import ThumbnailsType
from auctions.db.models.images import Image
from auctions.db.models.items import Item
from auctions.db.repositories.images import ImagesRepository


class ImagesService:
    def __init__(self, images_repository: ImagesRepository) -> None:
        self.images_repository = images_repository

        config: Config = current_app.config["config"]

        self.base_dir = config.BASE_DIR
        self.assets_path = config.assets_path
        self.images_path = config.images_path
        self.full_images_path = config.full_images_path
        self.thumbnails = config.thumbnails
        self.separators_path = config.separators_path
        self.separators_generated_path = config.separators_generated_path
        self.separators_text_file_path = config.separators_text_file_path
        self.separators_font_file_path = config.separators_font_file_path
        self.separators_start_price_position = config.separators_start_price_position
        self.separators_min_step_position = config.separators_min_step_position

        self.orientation_rotation_map = {
            3: 180,
            6: 270,
            8: 90,
        }

    def bulk_upload(self, files: list[FileStorage]) -> list[Image]:
        images = []

        for file in files:
            images.append(self.upload_one(file))

        return images

    def upload_one(self, file: FileStorage) -> Image:
        mime_type, _ = guess_type(file.filename)
        file_extension = guess_extension(mime_type)
        image_uuid = str(uuid4())
        file_name = f"{image_uuid}{file_extension}"

        urls = {
            "full": self.full_images_path / file_name,
            **{thumbnail_type: thumbnail["path"] / file_name for thumbnail_type, thumbnail in self.thumbnails.items()},
        }

        if not self.full_images_path.exists():
            try:
                self.full_images_path.mkdir(parents=True)
            except FileExistsError:
                pass

        try:
            self.save_and_normalize(file, urls["full"])
            self.make_thumbs(urls)

            return self.images_repository.create(
                mime_type=mime_type,
                urls={key: str(value.as_posix()) for key, value in urls.items()},
                is_main=True,
            )
        except Exception:
            for path in urls.values():
                path.unlink(missing_ok=True)

            raise

    @staticmethod
    def save_and_normalize(file: FileStorage, save_path: Path) -> None:
        temp_path = Path(save_path.name).absolute()
        file.save(temp_path)
        file.close()

        try:
            image = pyvips.Image.new_from_file(str(temp_path))
            image = image.autorot()
            image.write_to_file(str(save_path), interlace=True, optimize_coding=True, strip=True)
        finally:
            temp_path.unlink(missing_ok=True)

    def make_thumbs(self, urls: dict[str, Path]) -> None:
        for thumbnail_type, thumbnail_data in self.thumbnails.items():
            self.make_thumb(urls["full"], urls[thumbnail_type], thumbnail_data)

    @staticmethod
    def make_thumb(source_path: Path, target_path: Path, thumbnail_data: ThumbnailsType) -> None:
        thumb = pyvips.Image.thumbnail(str(source_path), thumbnail_data["bounds"][0])
        thumb.write_to_file(str(target_path))

    @staticmethod
    def scan_barcode(image: Image) -> tuple[Optional[str], Optional[str]]:
        pillow_image = PillowImage.open(image.urls["full"])

        codes = decode(pillow_image, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN5, ZBarSymbol.UPCA])

        upca = None
        ean13 = None
        ean5 = None

        for code in codes:
            if code.type == "UPCA":
                upca = code.data.decode("utf-8")
            elif code.type == "EAN13":
                ean13 = code.data.decode("utf-8")
            elif code.type == "EAN5":
                ean5 = code.data.decode("utf-8")

        return upca or ean13, ean5

    def delete_for_item(self, item: Item) -> None:
        self.images_repository.delete(item.images)
