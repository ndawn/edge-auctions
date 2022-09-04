from typing import Type

from sqlalchemy import delete

from auctions.db.models.auction_targets import AuctionTarget
from auctions.db.models.auction_targets import AuctionTarget_ExternalEntity
from auctions.db.repositories.base import Repository
from auctions.db.repositories.external import ExternalRepositoryMixin


class AuctionTargetsRepository(Repository[AuctionTarget], ExternalRepositoryMixin):
    joined_fields = (AuctionTarget.external,)
    external_table = AuctionTarget_ExternalEntity
    model_id = "target_id"

    @property
    def model(self) -> Type[AuctionTarget]:
        return AuctionTarget

    def delete(self, instances: list[AuctionTarget]) -> None:
        instance_ids = [instance.id for instance in instances]

        self.session.execute(
            delete(AuctionTarget_ExternalEntity).where(AuctionTarget_ExternalEntity.c.target_id.in_(instance_ids))
        )

        self.session.execute(delete(AuctionTarget).where(AuctionTarget.id.in_(instance_ids)))
