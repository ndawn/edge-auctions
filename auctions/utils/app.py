from functools import wraps

from argon2 import PasswordHasher
from flask import Flask
from flask_mail import Mail

from auctions.config import Config
from auctions.db import db
from auctions.dependencies import provider
from auctions.utils.cipher import AESCipher


def create_base_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
    app.config["SQLALCHEMY_ECHO"] = config.debug
    db.init_app(app)

    mail = Mail(app)

    provider.add_global(config)
    provider.add_global(PasswordHasher())
    provider.add_global(AESCipher(config.password_key))
    provider.add_global(mail)

    return app


def with_app_context(app: Flask) -> callable:
    def decorator(func: callable) -> callable:
        @wraps(func)
        def decorated(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)

        return decorated

    return decorator
