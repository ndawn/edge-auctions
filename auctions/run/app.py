from authlib.integrations.flask_client import OAuth
from dramatiq import set_broker
from dramatiq.brokers.redis import RedisBroker
from flask import jsonify
from flask import Flask

from auctions.config import Config
from auctions.dependencies import provider
from auctions.endpoints import root_blueprint
from auctions.utils.app import create_base_app
from auctions.utils.login import require_auth
from auctions.utils.token_validator import Auth0JWTBearerTokenValidator
from uvicorn_config import run_configured

from flask_cors import CORS


def create_oauth(app: Flask, config: Config) -> OAuth:
    app.secret_key = config.auth0_app_secret_key

    oauth = OAuth(app)

    oauth.register(
        "edge_auctions_admin",
        client_id=config.auth0_admin_client_id,
        client_secret=config.auth0_admin_client_secret,
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f"https://{config.auth0_domain}/.well-known/openid-configuration",
    )

    # oauth.register(
    #     "edge_auctions",
    #     client_id=config.auth0_client_id,
    #     client_secret=config.auth0_client_secret,
    #     client_kwargs={"scope": "openid profile email"},
    #     server_metadata_url=f"https://{config.auth0_domain}/.well-known/openid-configuration",
    # )

    validator = Auth0JWTBearerTokenValidator(config.auth0_domain, config.auth0_api_identifier)
    require_auth.register_token_validator(validator)

    return oauth


def create_app(config: Config) -> Flask:
    app = create_base_app(config)
    oauth = create_oauth(app, config)
    broker = RedisBroker(url=config.broker_url)
    set_broker(broker)

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

    app.register_blueprint(root_blueprint)

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
