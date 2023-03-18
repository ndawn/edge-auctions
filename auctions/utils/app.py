from argon2 import PasswordHasher
from flask import Flask as BaseFlask
# from flask_mail import Mail

from auctions.config import Config
from auctions.db.session import SessionManager
from auctions.dependencies import DependencyProvider
from auctions.utils.cipher import AESCipher


class Flask(BaseFlask):
    provider: DependencyProvider


def create_base_app(config: Config) -> Flask:
    app = Flask(__name__)
    session_manager = SessionManager(config)

    # @app.teardown_request
    # def remove_session(_) -> None:
    #     session_manager.session.remove()

    # mail = Mail(app)

    provider = DependencyProvider(app)
    app.provider = provider

    provider.add_global(config)
    provider.add_global(session_manager)
    provider.add_global(PasswordHasher())
    provider.add_global(AESCipher(config.password_key))
    # provider.add_global(mail)

    return app
