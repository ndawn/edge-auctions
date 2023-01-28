import sys
from multiprocessing import cpu_count

import uvicorn


def run_configured(app):
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=1337,
        workers=cpu_count() + 1,
        interface="wsgi",
        log_level="debug",
    )

    server = uvicorn.Server(config)
    server.run()
