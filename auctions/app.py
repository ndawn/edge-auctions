import os
import sys
from importlib import import_module

import loguru

from auctions.config import Config


@loguru.logger.catch
def main() -> None:
    run_mode = os.getenv("RUN_MODE", "")
    config = Config.load(os.getenv("CONFIG_PATH", ""))

    if config.vips_dir:
        os.environ["PATH"] = os.pathsep.join((config.vips_dir, os.environ["PATH"]))

    loguru.logger.add(
        f"logs/app_{run_mode}_{{time}}.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    loguru.logger.info(f"Starting in run mode: {run_mode}")
    module = import_module(f"auctions.run.{run_mode}")
    module.main(config)


if __name__ == "__main__":
    main()
