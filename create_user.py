import argparse
import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from auctions.db.repositories.users import UsersRepository
from auctions.services.users_service import UsersService


parser = argparse.ArgumentParser()
parser.add_argument("command", nargs=1, choices=["create", "delete", "clear"], required=True)
parser.add_argument("-u", "--user")
parser.add_argument("-p", "--password")
parser.add_argument("-n", "--name")
parser.add_argument("-l", "--last-name")


def execute(argv: list[str]) -> None:
    args = parser.parse_args(argv)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    with app.app_context():
        SQLAlchemy(app)
        service = UsersService(None, UsersRepository())  # type: ignore

        service.create_user(
            username=sys.argv[1],
            password=sys.argv[2],
            first_name=sys.argv[3],
            last_name=sys.argv[4],
        )


if __name__ == "__main__":
    execute(sys.argv[1:])
