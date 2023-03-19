import subprocess
from signal import SIGINT

from auctions.config import Config


def run_queue(config: Config) -> None:
    process = subprocess.Popen(["dramatiq", "auctions.tasks"], shell=True)

    try:
        process.wait()
    except (KeyboardInterrupt, SystemExit):
        process.send_signal(SIGINT)
        process.wait(5)


def main(config: Config) -> None:
    run_queue(config)
