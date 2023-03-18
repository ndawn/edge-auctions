from importlib import import_module
from pkgutil import iter_modules

from flask import Blueprint
from flask import Flask


exclude = {"crud"}


def connect_blueprints(app: Flask) -> Blueprint:
    root_blueprint = Blueprint("root", __name__)

    for module_spec in iter_modules([__name__.replace(".", "/")]):
        if module_spec.ispkg or module_spec.name in exclude:
            continue

        module = import_module(f"{__name__}.{module_spec.name}")
        root_blueprint.register_blueprint(module.blueprint)

    app.register_blueprint(root_blueprint)
    return root_blueprint
