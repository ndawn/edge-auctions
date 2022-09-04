from celery import Celery
from celery.exceptions import Retry

from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.exceptions import AuctionReschedule
from auctions.services.auctions_service import AuctionsService

celery = Celery("tasks")


@celery.task
@inject
def close_auction(
    auction_id: int,
    auctions_service: AuctionsService = Provide["auctions_service"],
) -> None:
    try:
        auctions_service.close_auction(auction_id)
    except AuctionReschedule as exception:
        raise Retry(exc=exception, when=exception.execute_at) from exception


@celery.task
@inject
def close_auction_set(
    set_id: int,
    auctions_service: AuctionsService = Provide["auctions_service"],
) -> None:
    try:
        auctions_service.close_auction_set(set_id)
    except AuctionReschedule as exception:
        raise Retry(exc=exception, when=exception.execute_at) from exception
