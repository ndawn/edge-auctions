from io import BytesIO
from mimetypes import guess_extension
from mimetypes import guess_type
from pathlib import Path
from typing import Optional
from uuid import uuid4

from exif import Image as ExifImage
from exif._constants import Orientation
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
            Orientation.BOTTOM_RIGHT: PillowImage.ROTATE_180,
            Orientation.RIGHT_TOP: PillowImage.ROTATE_270,
            Orientation.LEFT_BOTTOM: PillowImage.ROTATE_90,
        }

    def bulk_upload(self, files: list[FileStorage]) -> list[Image]:
        images = []

        for file in files:
            images.append(self.upload_one(file))

        return images

    def upload_one(self, file: FileStorage) -> Image:
        mime_type, _ = guess_type(file.filename)
        file_format = mime_type.split("/")[1]
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
            file_buffer = BytesIO(file.stream.read())
            file.close()

            file_buffer = self._normalize_orientation(file_buffer, file_format)

            with open(urls["full"], "wb") as full_image_file:
                full_image_file.write(file_buffer.getvalue())

            self.make_thumbs(file_buffer, urls)

            return self.images_repository.create(
                mime_type=mime_type,
                urls={key: value.relative_to(self.base_dir).as_posix() for key, value in urls.items()},
                is_main=True,
            )
        except Exception:
            for path in urls.values():
                path.unlink(missing_ok=True)

            raise

    def make_thumbs(self, raw_image: BytesIO, urls: dict[str, Path]) -> None:
        for thumbnail_type, thumbnail_data in self.thumbnails.items():
            self.make_thumb(raw_image, urls[thumbnail_type], thumbnail_data)

    @staticmethod
    def make_thumb(
        raw_image: BytesIO,
        save_path: Path,
        thumbnail_data: ThumbnailsType,
    ) -> None:
        thumb = PillowImage.open(raw_image)
        thumb.thumbnail(thumbnail_data["bounds"], PillowImage.ANTIALIAS)
        thumb.save(save_path)

    def _normalize_orientation(self, raw_image: BytesIO, file_format: str) -> BytesIO:
        exif_data = ExifImage(raw_image)
        exif_orientation = Orientation.TOP_LEFT

        if exif_data.has_exif:
            try:
                exif_orientation = exif_data["orientation"]
            except KeyError:
                pass

        image = PillowImage.open(raw_image)

        image_data = list(image.getdata())
        image = PillowImage.new(image.mode, image.size)
        image.putdata(image_data)

        rotation = self.orientation_rotation_map.get(exif_orientation)

        if rotation is not None:
            image = image.transpose(rotation)

        raw_image.truncate(0)
        raw_image.seek(0)
        image.save(raw_image, format=file_format)
        return raw_image

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
