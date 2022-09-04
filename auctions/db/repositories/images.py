from pathlib import Path
from typing import Type
from typing import Union

from flask import current_app

from auctions.db.models.images import Image
from auctions.db.repositories.base import Repository


class ImagesRepository(Repository[Image]):
    joined_fields = ()

    @property
    def model(self) -> Type[Image]:
        return Image

    def delete(self, instances: Union[Image, list[Image]]) -> None:
        base_dir: Path = current_app.config["config"].BASE_DIR

        if not isinstance(instances, list):
            instances = [instances]

        for instance in instances:
            for path in instance.urls.values():
                if path:
                    (base_dir / path).unlink(missing_ok=True)

        if not base_dir.exists():
            base_dir.mkdir(exist_ok=True)

        super().delete(instances)
