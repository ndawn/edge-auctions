import logging

import dramatiq
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.blocking import BlockingScheduler
from dramatiq.brokers.redis import RedisBroker

from auctions.config import Config
from auctions.jobs import periodic_auction_set_check
from auctions.jobs import periodic_invoice_check


def create_scheduler(config: Config) -> BlockingScheduler:
    broker = RedisBroker(url=config.broker_url, middleware=[])
    dramatiq.set_broker(broker)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        periodic_auction_set_check,
        "interval",
        id="periodic_auction_set_check",
        seconds=10,
        max_instances=1,
    )
    scheduler.add_job(
        periodic_invoice_check,
        "interval",
        id="periodic_invoice_check",
        seconds=30,
        max_instances=1,
    )

    return scheduler


def main(config: Config) -> None:
    scheduler = create_scheduler(config)
    logging.basicConfig(level=logging.DEBUG)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        try:
            scheduler.shutdown()
        except SchedulerNotRunningError:
            pass
