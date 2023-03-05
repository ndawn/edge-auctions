import os

from auctions.db.models.images import Image
from auctions.db.repositories.base import Repository


class ImagesRepository(Repository[Image]):
    joined_fields = ()

    @property
    def model(self) -> type[Image]:
        return Image

    def delete(self, instances: Image | list[Image]) -> None:
        if not isinstance(instances, list):
            instances = [instances]

        for instance in instances:
            for path in instance.urls.values():
                if path and os.path.exists(path):
                    os.unlink(path)

        super().delete(instances)
