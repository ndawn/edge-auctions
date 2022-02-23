from dataclasses import dataclass
import os.path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


IMAGE_NAME_PATTERN = 'sep_%s_%s.png'


@dataclass
class SeparatorBackground:
    ceil_price: int
    path: str


class SeparatorFactory:
    def __init__(self, config: dict):
        self.__config = config
        self._image_storage_path = config['storage']
        self._text_image_path = config['text']
        self._start_price_position = config['start_price_position']
        self._min_step_position = config['min_step_position']
        self._font = config['font']
        self._backgrounds = sorted(
            [
                SeparatorBackground(ceil_price=ceil_price, path=path)
                for ceil_price, path in config['variations'].items()
            ],
            key=lambda bg: bg.ceil_price,
            reverse=True,
        )

    def _get_background(self, start_price: int) -> Optional[str]:
        for background in self._backgrounds:
            if background.ceil_price >= start_price:
                return background.path
        return self._backgrounds[0].path

    def compose(self, start_price: int, min_step: int) -> str:
        image_file_name = IMAGE_NAME_PATTERN % (start_price, min_step)
        image_file_path = os.path.join(self._image_storage_path, image_file_name)

        if os.path.exists(image_file_path):
            return image_file_path

        font = ImageFont.truetype(self._font, size=380)

        text_image = Image.open(self._text_image_path)
        background_image = Image.open(self._get_background(start_price))

        result_image = Image.new('RGBA', background_image.size)
        result_image.paste(background_image)
        result_image.paste(text_image, (0, 0), text_image)

        drawer = ImageDraw.Draw(result_image)
        drawer.text(
            xy=self._start_price_position,
            text=str(start_price),
            fill=(255, 255, 255),
            font=font,
        )
        drawer.text(
            xy=self._min_step_position,
            text=str(min_step),
            fill=(255, 255, 255),
            font=font,
        )
        result_image.save(image_file_path)
        return image_file_path
