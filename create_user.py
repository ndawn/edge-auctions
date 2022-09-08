import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from auctions.db.repositories.users import UsersRepository
from auctions.services.users_service import UsersService


app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

with app.app_context():
    db = SQLAlchemy(os.getenv("DB_URL"))

    service = UsersService(None, UsersRepository())  # type: ignore

    service.create_user(
        username=sys.argv[1],
        password=sys.argv[2],
        first_name=sys.argv[3],
        last_name=sys.argv[4],
    )
