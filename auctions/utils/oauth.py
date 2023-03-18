from flask import Flask
from authlib.integrations.flask_client import OAuth

from auctions.config import Config
from auctions.utils.resource_protector import require_auth
from auctions.utils.token_validator import Auth0JWTBearerTokenValidator


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
