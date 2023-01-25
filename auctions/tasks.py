import os
from datetime import datetime
from datetime import timezone
from functools import wraps

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.errors import Retry
from dramatiq.middleware.group_callbacks import GroupCallbacks
from dramatiq.rate_limits.backends.redis import RedisBackend as RedisRateLimiterBackend
from dramatiq.results import Results
from dramatiq.results.backends.redis import RedisBackend as RedisResultBackend
from flask import Flask


from auctions.config import Config
from auctions.dependencies import DependencyProvider
from auctions.dependencies import inject
from auctions.exceptions import AuctionReschedule
from auctions.services.auctions_service import AuctionsService
from auctions.utils.app import create_base_app


broker = None


def create_broker(config_: Config) -> dramatiq.Broker:
    broker_ = RedisBroker(url=config_.broker_url)
    backend = RedisResultBackend(url=config_.result_backend_url)
    rate_limiter_backend = RedisRateLimiterBackend(url=config_.result_backend_url)
    broker_.add_middleware(Results(backend=backend, result_ttl=config_.result_ttl_ms))
    broker_.add_middleware(GroupCallbacks(rate_limiter_backend))

    return broker_


def with_app_context(app: Flask) -> callable:
    def decorator(func: callable) -> callable:
        @wraps(func)
        def decorated(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)

        return decorated

    return decorator


@inject
def close_auction(auction_id: int, auctions_service: AuctionsService) -> str:
    try:
        auction = auctions_service.close_auction(auction_id)
        return str(auction.ended_at)
    except AuctionReschedule as exception:
        raise Retry(
            message=str(exception),
            delay=(exception.execute_at - datetime.now(timezone.utc)).seconds * 1000,
        ) from exception


@inject
def close_auction_set(set_id: int, auctions_service: AuctionsService) -> str:
    try:
        auction_set = auctions_service.close_auction_set(set_id)
        return str(auction_set.ended_at)
    except AuctionReschedule as exception:
        raise Retry(
            message=str(exception),
            delay=(exception.execute_at - datetime.now(timezone.utc)).seconds * 1000,
        ) from exception


if os.getenv("RUN_MODE", "") == "worker":
    config = Config.load(os.getenv("CONFIG_PATH", ""))
    app = create_base_app(config)
    DependencyProvider.add_global("config", config)
    broker = create_broker(config)
    dramatiq.set_broker(broker)

    close_auction = dramatiq.actor(store_results=True)(with_app_context(app)(close_auction))
    close_auction_set = dramatiq.actor(store_results=True)(with_app_context(app)(close_auction_set))
