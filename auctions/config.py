import os
from pathlib import Path
from typing import Optional
from typing import TypedDict

from yaml import FullLoader
from yaml import load


class ThumbnailsType(TypedDict):
    path: Path
    bounds: tuple[int, int]


class SeparatorsType(TypedDict):
    path: str
    generated_path: str
    text_file_path: str
    font_file_path: str
    start_price_position: tuple[int, int]
    min_step_position: tuple[int, int]


class VkType(TypedDict):
    v: str
    subscribe_id: int


class Config:
    __instance: Optional["Config"] = None

    BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def __new__(cls) -> "Config":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    def __init__(self) -> None:
        self.db_url: Optional[str] = None
        self.debug: Optional[bool] = None
        self.token_expire_time: Optional[int] = None
        self.assets_path: Optional[Path] = None
        self.images_path: Optional[Path] = None
        self.full_images_path: Optional[Path] = None
        self.thumbnails: dict[str, ThumbnailsType] = {}
        self.auction_close_interval: Optional[int] = None
        self.default_timezone: Optional[str] = None
        self.separators_path: Optional[Path] = None
        self.separators_generated_path: Optional[Path] = None
        self.separators_text_file_path: Optional[Path] = None
        self.separators_font_file_path: Optional[Path] = None
        self.separators_start_price_position: Optional[tuple[int, int]] = None
        self.separators_min_step_position: Optional[tuple[int, int]] = None
        self.celery: dict[str, str] = {}
        self.vk: Optional[VkType] = None
        self.rate_limits: dict[str, int] = {}
        self.dirs: list[Path] = []

    def load(self, file_name: str) -> None:
        with open(file_name, encoding="utf-8") as config_file:
            config_raw = load(config_file, FullLoader)

        self._parse_config(**config_raw)

    def _parse_config(
        self,
        db_url: str,
        debug: bool,
        token_expire_time: int,
        assets_path: str,
        images_path: str,
        full_images_path: str,
        thumbnails: dict[str, ThumbnailsType],
        auction_close_interval: int,
        default_timezone: str,
        separators: SeparatorsType,
        celery: dict[str, str],
        vk: VkType,
        rate_limits: dict[str, int],
    ) -> None:
        self.db_url = db_url
        self.debug = debug
        self.token_expire_time = token_expire_time
        self.assets_path = Config.BASE_DIR / assets_path
        self.images_path = Config.BASE_DIR / images_path
        self.full_images_path = Config.BASE_DIR / full_images_path
        self.auction_close_interval = auction_close_interval
        self.default_timezone = default_timezone
        self.separators_path = Config.BASE_DIR / separators["path"]
        self.separators_generated_path = Config.BASE_DIR / separators["generated_path"]
        self.separators_text_file_path = Config.BASE_DIR / separators["text_file_path"]
        self.separators_font_file_path = Config.BASE_DIR / separators["font_file_path"]
        self.separators_start_price_position = separators["start_price_position"]
        self.separators_min_step_position = separators["min_step_position"]
        self.thumbnails = self._process_thumbnail_config(thumbnails)
        self.celery = celery
        self.vk = vk
        self.rate_limits = rate_limits

        self.dirs = [
            self.assets_path,
            self.images_path,
            self.full_images_path,
            self.separators_path,
            self.separators_generated_path,
            *(thumbnail_path["path"] for thumbnail_path in self.thumbnails.values()),
        ]

        self._create_dirs()

    def _create_dirs(self) -> None:
        for path in self.dirs:
            if not path.exists():
                path.mkdir()

    def _process_thumbnail_config(self, data: dict[str, ThumbnailsType]) -> dict[str, ThumbnailsType]:
        processed = {}

        for thumbnail_type, config in data.items():
            processed[thumbnail_type] = ThumbnailsType(
                path=self.BASE_DIR / Path(config["path"]),
                bounds=tuple(config["bounds"]),
            )

        return processed


# AWS_ACCESS_KEY_ID = 'AKIA3BLSMFREKUUQGA5C'
# AWS_SECRET_ACCESS_KEY = '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'
# AWS_STORAGE_BUCKET_NAME = 'edge-auctions'
# AWS_DEFAULT_ACL = 'public-read'
# AWS_S3_REGION_NAME = 'eu-north-1'
