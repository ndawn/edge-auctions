from dramatiq import set_broker
from dramatiq.brokers.redis import RedisBroker
from flask import jsonify
from flask import Flask

from auctions.config import Config
from auctions.dependencies import DependencyProvider
from auctions.endpoints import connect_blueprints
from auctions.utils.app import create_base_app
from auctions.utils.error_handler import handle_exception
from auctions.utils.oauth import create_oauth
from uvicorn_config import run_configured

from flask_cors import CORS


def create_app(config: Config) -> Flask:
    app = create_base_app(config)
    oauth = create_oauth(app, config)
    broker = RedisBroker(url=config.broker_url)
    set_broker(broker)

    provider = DependencyProvider(app)
    provider.add_global(oauth)

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

    app.errorhandler(Exception)(handle_exception)

    connect_blueprints(app)
    return app


def run_app(config: Config) -> None:
    app = create_app(config)

    try:
        if config.debug:
            CORS(app)
            app.run(debug=config.debug, host="0.0.0.0")
        else:
            run_configured(app)
    except (KeyboardInterrupt, SystemExit):
        pass


def main(config: Config) -> None:
    run_app(config)
