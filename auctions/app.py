import os
import subprocess
import sys

from dramatiq import set_broker
from flask import Flask
from flask import jsonify

from auctions.config import Config
from auctions.dependencies import DependencyProvider
from auctions.endpoints import root_blueprint
from auctions.tasks import create_broker
from auctions.utils.app import create_base_app
from uvicorn_config import run_configured

from flask_cors import CORS


def create_app(config: Config) -> Flask:
    app = create_base_app(config)
    broker = create_broker(config)
    set_broker(broker)

    DependencyProvider.add_global("config", config)

    @app.errorhandler(422)
    @app.errorhandler(405)
    @app.errorhandler(404)
    @app.errorhandler(400)
    def handle_error(err):
        headers = getattr(err, "data", {}).get("headers", None)
        messages = getattr(err, "data", {}).get("messages", ["Invalid request"])

        response_data = {
            "error": err.__class__.__name__,
            "message": ", ".join(messages),
            "status_code": err.code,
        }

        if headers:
            return jsonify(response_data), err.code, headers

        return jsonify(response_data), err.code

    app.register_blueprint(root_blueprint)

    return app


def run_app(config: Config) -> None:
    app = create_app(config)

    if config.debug:
        CORS(app)
        app.run(
            debug=config.debug,
            host="0.0.0.0",
            ssl_context=(config.local_cert_path, config.local_cert_key_path),
        )
    else:
        run_configured(app)


def run_worker(config: Config) -> None:
    result = subprocess.run([
        "dramatiq",
        "--log-file",
        str(config.tasks_log_path),
        "auctions.tasks",
    ])
    sys.exit(result.returncode)


def main() -> None:
    run_mode = os.getenv("RUN_MODE", "")
    config = Config.load(os.getenv("CONFIG_PATH", ""))

    {
        "app": run_app,
        "worker": run_worker,
    }.get(run_mode, lambda _: print(f"Unrecognized run mode: {run_mode}"))(config)


if __name__ == "__main__":
    main()
