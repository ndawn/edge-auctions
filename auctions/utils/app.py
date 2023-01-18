from argon2 import PasswordHasher
from flask import Flask

from auctions.config import Config
from auctions.db import db


def create_base_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
    app.config["SQLALCHEMY_ECHO"] = config.debug
    app.config["PASSWORD_HASHER"] = PasswordHasher()
    db.init_app(app)

    return app
