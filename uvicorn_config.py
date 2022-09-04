from multiprocessing import cpu_count

import uvicorn


def run_configured(app):
    config = uvicorn.Config(
        app,
        uds="/sockets/gunicorn.sock",
        workers=cpu_count() + 1,
        interface="wsgi",
        log_level="debug",
    )

    server = uvicorn.Server(config)
    server.run()
