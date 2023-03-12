from traceback import print_exception

from auctions.db.models.auctions import Auction
from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.enum import EmailType
from auctions.db.models.enum import PushEventType
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.dependencies import inject
from auctions.dependencies import Provide
from auctions.exceptions import ObjectDoesNotExist
from auctions.services.auctions_service import AuctionsService
from auctions.services.email_service import EmailService
from auctions.services.push_service import PushService
from auctions.services.shop_connect_service import ShopConnectService
from auctions.services.users_service import UsersService


@inject
def try_close_auction_sets(auctions_service: AuctionsService = Provide()) -> None:
    try:
        auction_sets = auctions_service.auction_sets_repository.get_many(AuctionSet.ended_at.is_(None))

        for auction_set in auction_sets:
            auctions_service.close_auction_set(auction_set)
    except Exception as exception:
        print_exception(type(exception), exception, exception.__traceback__)


@inject
def create_invoice(
    user_id: str,
    auction_ids: list[int],
    shop_connect_service: ShopConnectService = Provide(),
    users_service: UsersService = Provide(),
    auctions_repository: AuctionsRepository = Provide(),
) -> None:
    try:
        user = users_service.get_user(user_id)
        auctions = auctions_repository.get_many(ids=auction_ids)
        shop_connect_service.create_invoice(user, auctions)
    except Exception as exception:
        print_exception(type(exception), exception, exception.__traceback__)


@inject
def check_invoices(
    auctions_service: AuctionsService = Provide(),
    auctions_repository: AuctionsRepository = Provide(),
) -> None:
    try:
        auctions = auctions_repository.get_many(Auction.invoice_link.is_not(None))
        auctions_service.check_invoices(auctions)
    except Exception as exception:
        print_exception(type(exception), exception, exception.__traceback__)


@inject
def send_push(
    recipient_id: str,
    event_type: PushEventType,
    payload: ...,
    users_service: UsersService = Provide(),
    push_service: PushService = Provide(),
) -> None:
    try:
        recipient = users_service.get_user(recipient_id)
    except ObjectDoesNotExist:
        return

    push_service.send_event(recipient, event_type, payload)


@inject
def send_email(
    recipient_id: str,
    message_type: EmailType,
    users_service: UsersService = Provide(),
    email_service: EmailService = Provide(),
) -> None:
    try:
        recipient = users_service.get_user(recipient_id)
        email_service.send_email(recipient, message_type)
    except Exception as exception:
        print_exception(type(exception), exception, exception.__traceback__)


tasks = [
    check_invoices,
    create_invoice,
    send_push,
    try_close_auction_sets,
]
