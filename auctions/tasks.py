import os
from traceback import print_exception

import dramatiq
import firebase_admin
import loguru
from argon2 import PasswordHasher
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker

from auctions.config import Config
from auctions.db.models.auctions import Auction
from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.enum import PushEventType
from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.push import PushSubscriptionsRepository
from auctions.db.repositories.users import UsersRepository
from auctions.exceptions import ObjectDoesNotExist
from auctions.services.auctions_service import AuctionsService
from auctions.services.auth_service import AuthService
from auctions.services.password_service import PasswordService
from auctions.services.push_service import PushService
from auctions.services.schedule_service import ScheduleService
from auctions.services.shop_connect_service import ShopConnectService
from auctions.utils.cipher import AESCipher


config = Config.load(os.getenv("CONFIG_PATH"))
engine = create_engine(config.db_url, echo=config.debug)
session_class = scoped_session(sessionmaker(engine))

broker = RedisBroker(url=config.broker_url)
dramatiq.set_broker(broker)

firebase_admin.initialize_app()

auctions_repository = AuctionsRepository(session=session_class, config=config)  # noqa
auction_sets_repository = AuctionSetsRepository(session=session_class, config=config)  # noqa
push_subscriptions_repository = PushSubscriptionsRepository(session=session_class, config=config)  # noqa
users_repository = UsersRepository(session=session_class, config=config)  # noqa

schedule_service = ScheduleService()

auctions_service = AuctionsService(
    auction_sets_repository=auction_sets_repository,
    auctions_repository=auctions_repository,
    schedule_service=schedule_service,
    config=config,
)


shop_connect_service = ShopConnectService(
    password_service=PasswordService(
        password_cipher=AESCipher(config.password_key),
        password_hasher=PasswordHasher(),
        config=config,
    ),
    schedule_service=schedule_service,
    auctions_repository=auctions_repository,
    config=config,
)


auth_service = AuthService(shop_connect_service=shop_connect_service, users_repository=users_repository, config=config)
push_service = PushService(
    push_subscriptions_repository=push_subscriptions_repository,
    config=config,
)


@dramatiq.actor(max_retries=0)
@loguru.logger.catch
def try_close_auction_sets() -> None:
    auction_sets = auctions_service.auction_sets_repository.get_many(AuctionSet.ended_at.is_(None))

    for auction_set in auction_sets:
        auctions_service.close_auction_set(auction_set)

    session_class.commit()
    session_class.remove()


@dramatiq.actor(max_retries=0)
@loguru.logger.catch
def create_invoice(user_id: str, auction_ids: list[int]) -> None:
    user = auth_service.get_user_by_id(user_id)
    auctions = auctions_repository.get_many(ids=auction_ids)
    shop_connect_service.create_invoice(user, auctions)
    session_class.commit()
    session_class.remove()


@dramatiq.actor(max_retries=0)
@loguru.logger.catch
def check_invoices() -> None:
    auctions = auctions_repository.get_many(Auction.invoice_link.is_not(None))
    auctions_service.check_invoices(auctions)
    session_class.commit()
    session_class.remove()


@dramatiq.actor(max_retries=0)
@loguru.logger.catch
def send_push(recipient_id: str, event_type: PushEventType, payload: ...) -> None:
    try:
        recipient = auth_service.get_user_by_id(recipient_id)
    except ObjectDoesNotExist:
        return

    push_service.send_event(recipient, event_type, payload)
    session_class.commit()
    session_class.remove()
