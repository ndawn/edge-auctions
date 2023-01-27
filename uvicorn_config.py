import sys
from multiprocessing import cpu_count

import uvicorn


def run_configured(app):
    bind_kwargs = {}

    if sys.platform == "win32":
        bind_kwargs["port"] = 1337
    else:
        bind_kwargs["uds"] = "./sockets/app.sock"

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
