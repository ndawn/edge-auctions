from argon2 import PasswordHasher
from flask import Flask
from flask import jsonify
from werkzeug.middleware.profiler import ProfilerMiddleware

from auctions.config import Config
from auctions.db import db
from auctions.endpoints import root_blueprint
from auctions.tasks import celery
from uvicorn_config import run_configured


def create_app() -> Flask:
    app = Flask(__name__)
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
    config = Config()
    config.load("config.yml")
    app.config["config"] = config
    app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
    app.config["SQLALCHEMY_ECHO"] = config.debug
    app.config["PASSWORD_HASHER"] = PasswordHasher()
    db.init_app(app)

    celery.config_from_object(config.celery)

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


app = create_app()


if __name__ == "__main__":
    if app.config["config"].debug:
        app.run(debug=app.config["config"].debug)
    else:
        run_configured(app)
