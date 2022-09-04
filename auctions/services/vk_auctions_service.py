from datetime import datetime
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo

from flask import current_app

from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auctions import Auction
from auctions.db.models.enum import ExternalSource
from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.external import ExternalEntitiesRepository
from auctions.exceptions import AuctionCloseFailed
from auctions.exceptions import AuctionReschedule
from auctions.services.vk_request_service import VKRequestService
from auctions.utils.templates import build_description


class VKAuctionsService:
    def __init__(
        self,
        vk_request_service: VKRequestService,
        auction_sets_repository: AuctionSetsRepository,
        auctions_repository: AuctionsRepository,
        external_entities_repository: ExternalEntitiesRepository,
    ) -> None:
        self.vk_request_service = vk_request_service
        self.auction_sets_repository = auction_sets_repository
        self.auctions_repository = auctions_repository
        self.external_entities_repository = external_entities_repository

        self.auction_close_interval = current_app.config["config"].auction_close_interval
        self.default_timezone = current_app.config["config"].default_timezone

    def upload_auctions(self, auction_set: AuctionSet) -> None:
        group_id = int(auction_set.target.get_external(ExternalSource.VK).entity_id)
        date_due_utc = auction_set.date_due.replace(tzinfo=timezone.utc)
        tzinfo = ZoneInfo(self.default_timezone)
        album_name = f'Аукционы до {date_due_utc.astimezone(tzinfo).strftime("%d.%m")}'
        if current_app.config['config'].debug:
            album_name = f'[Тест] {album_name}'
        album_id, upload_url = self.vk_request_service.create_album(group_id=group_id, title=album_name)

        external_auction_set = self.external_entities_repository.create(
            source=ExternalSource.VK,
            entity_id=str(album_id),
            extra={"upload_url": upload_url},
        )

        self.auction_sets_repository.add_external(auction_set, external_auction_set)

        for auction in auction_set.auctions:
            self.upload_auction(auction)

    def upload_auction(self, auction: Auction) -> None:
        group_id = int(auction.set.target.get_external(ExternalSource.VK).entity_id)
        album = auction.set.get_external(ExternalSource.VK)
        description = build_description(auction)

        photo_id = self.vk_request_service.upload_photo(
            group_id=group_id,
            album_id=album.entity_id,
            photo_url=auction.photo_url,
            description=description,
        )

        external_auction = self.external_entities_repository.create(
            source=ExternalSource.VK,
            entity_id=str(photo_id),
        )

        self.auctions_repository.add_external(auction, external_auction)

    @staticmethod
    def close_auction_set(auction_set: AuctionSet) -> None:
        auction_set.ended = datetime.utcnow()

    def close_auction(self, auction: Auction) -> None:
        now = datetime.utcnow()

        group_id = auction.set.target.get_external(ExternalSource.VK).entity_id
        external_auction = auction.get_external(ExternalSource.VK)

        if auction.date_due - timedelta(seconds=self.auction_close_interval) > now:
            raise AuctionReschedule(execute_at=auction.date_due)

        if auction.started_at is None:
            raise AuctionCloseFailed("Auction is not started yet")

        if not auction.is_active or auction.ended_at is not None:
            raise AuctionCloseFailed("Auction is already closed")

        auction.ended_at = now
        auction.is_active = False

        self.vk_request_service.send_comment(
            group_id=group_id,
            photo_id=external_auction.entity_id,
            message="Аукцион закрыт!",
        )
