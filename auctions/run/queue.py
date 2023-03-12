import argparse
import multiprocessing
import time

import dramatiq
from dramatiq import Worker
from dramatiq.brokers.redis import RedisBroker

from auctions.config import Config
from auctions.tasks import tasks
from auctions.utils.app import create_base_app
from auctions.utils.app import with_app_context


CPUS = multiprocessing.cpu_count()


def make_argument_parser():
    parser = argparse.ArgumentParser(
        prog="dramatiq",
        description="Run dramatiq workers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # parser.add_argument(
    #     "broker",
    #     help="the broker to use (eg: 'module' or 'module:a_broker')",
    # )
    # parser.add_argument(
    #     "modules", metavar="module", nargs="*",
    #     help="additional python modules to import",
    # )
    parser.add_argument(
        "--processes", "-p", default=CPUS, type=int,
        help="the number of worker processes to run (default: %s)" % CPUS,
    )
    parser.add_argument(
        "--threads", "-t", default=8, type=int,
        help="the number of worker threads per process (default: 8)",
    )
    parser.add_argument(
        "--path", "-P", default=".", nargs="*", type=str,
        help="the module import path (default: .)"
    )
    parser.add_argument(
        "--queues", "-Q", nargs="*", type=str,
        help="listen to a subset of queues (default: all queues)",
    )
    parser.add_argument(
        "--pid-file", type=str,
        help="write the PID of the master process to a file (default: no pid file)",
    )
    parser.add_argument(
        "--log-file", type=str,
        help="write all logs to a file (default: sys.stderr)",
    )
    parser.add_argument(
        "--skip-logging",
        action="store_true",
        help="do not call logging.basicConfig()"
    )
    parser.add_argument(
        "--use-spawn", action="store_true",
        help="start processes by spawning (default: fork on unix, spawn on windows)"
    )
    parser.add_argument(
        "--fork-function", "-f", action="append", dest="forks", default=[],
        help="fork a subprocess to run the given function"
    )
    parser.add_argument(
        "--worker-shutdown-timeout", type=int, default=600000,
        help="timeout for worker shutdown, in milliseconds (default: 10 minutes)"
    )

    parser.add_argument(
        "--watch",
        help=(
            "watch a directory and reload the workers when any source files "
            "change (this feature must only be used during development). "
            "This option is currently only supproted on unix systems."
        )
    )
    parser.add_argument(
        "--watch-use-polling",
        action="store_true",
        help=(
            "poll the filesystem for changes rather than using a "
            "system-dependent filesystem event emitter"
        )
    )

    parser.add_argument("--version", action="version", version=dramatiq.__version__)
    parser.add_argument("--verbose", "-v", action="count", default=0, help="turn on verbose log output")
    return parser


def run_queue(config: Config) -> None:
    broker = RedisBroker(url=config.broker_url, middleware=[])
    dramatiq.set_broker(broker)

    app = create_base_app(config)

    for task in tasks:
        dramatiq.actor(with_app_context(app)(task))

    worker = Worker(broker)
    worker.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        worker.stop()


def main(config: Config) -> None:
    run_queue(config)
