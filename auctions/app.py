import logging
import os
import sys
from importlib import import_module

from auctions.config import Config


def main() -> None:
    run_mode = os.getenv("RUN_MODE", "")
    config = Config.load(os.getenv("CONFIG_PATH", ""))

    try:
        module = import_module(f"auctions.run.{run_mode}")
        module.main(config)
    except ImportError:
        print(f"Unrecognized run mode: \"{run_mode}\"")
        sys.exit(1)


if __name__ == "__main__":
    main()
