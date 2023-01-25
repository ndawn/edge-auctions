from functools import reduce

from flask import request
from flask.blueprints import Blueprint
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.repositories.base import Model
from auctions.dependencies import inject
from auctions.serializers.base import BaseSerializer
from auctions.serializers.delete_object import DeleteObjectSerializer
from auctions.services.crud_service import CRUDServiceProvider
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import require_auth
from auctions.utils.misc import to_snake_case
from auctions.utils.response import JsonResponse


def bind_function_name(func: callable, name: str) -> callable:
    func.__name__ = name
    return func


def apply_decorators(func: callable, *decorators: callable) -> callable:
    return reduce(lambda func_, decorator: decorator(func_), decorators, func)


def create_crud_blueprint(
    model: type[Model],
    serializer_class: type[BaseSerializer],
    list_args: dict[str, ...] = None,
    create_args: dict[str, ...] | BaseSerializer = None,
    update_args: dict[str, ...] | BaseSerializer = None,
    operations: tuple[str, ...] = (
        "list",
        "create",
        "read",
        "update",
        "delete",
    ),
    protected: tuple[str, ...] = (
        "list",
        "create",
        "read",
        "update",
        "delete",
    ),
) -> Blueprint:
    name_singular = to_snake_case(model.__name__)
    name_plural = model.__tablename__

    all_list_args = {
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=10),
    }

    if list_args is not None:
        all_list_args.update(list_args)

    blueprint = Blueprint(name_plural, __name__, url_prefix=f"/{name_plural}")

    def list_objects(
        *,
        crud_service: CRUDServiceProvider,
        serializer: serializer_class,
    ) -> JsonResponse:
        args = parser.parse(all_list_args, request, location="query")
        instances = crud_service(model).list(**args)
        return JsonResponse(serializer.dump(instances, many=True))

    def get_object(
        *,
        id_: int,
        crud_service: CRUDServiceProvider,
        serializer: serializer_class,
    ) -> JsonResponse:
        instance = crud_service(model).get(id_)
        return JsonResponse(serializer.dump(instance))

    def create_object(
        *,
        crud_service: CRUDServiceProvider,
        serializer: serializer_class,
    ) -> JsonResponse:
        args = parser.parse(create_args, request, location="json")
        instance = crud_service(model).create(**args)
        return JsonResponse(serializer.dump(instance))

    def update_object(
        *,
        id_: int,
        crud_service: CRUDServiceProvider,
        serializer: serializer_class,
    ) -> JsonResponse:
        args = parser.parse(update_args, request, location="json")
        instance = crud_service(model).update(id_, **args)
        return JsonResponse(serializer.dump(instance))

    def delete_object(
        *,
        id_: int,
        crud_service: CRUDServiceProvider,
        delete_object_serializer: DeleteObjectSerializer,
    ) -> JsonResponse:
        crud_service(model).delete(id_)
        return JsonResponse(delete_object_serializer.dump(None))

    operations_spec = {
        "list": (list_objects, f"list_{name_plural}", blueprint.get, ""),
        "read": (get_object, f"get_{name_singular}", blueprint.get, "/<int:id_>"),
        "create": (create_object, f"create_{name_singular}", blueprint.post, ""),
        "update": (
            update_object,
            f"update_{name_singular}",
            blueprint.put,
            "/<int:id_>",
        ),
        "delete": (
            delete_object,
            f"delete_{name_singular}",
            blueprint.delete,
            "/<int:id_>",
        ),
    }

    for operation, (func, func_name, method, endpoint) in operations_spec.items():
        method: callable

        if operation not in operations:
            continue

        for operation_, args_object in [
            ("create", create_args),
            ("update", update_args),
        ]:
            if operation == operation_ and args_object is None:
                raise ValueError(f'Operation "{operation}" requires args to be set')

        if operation == "update" and update_args is None:
            raise ValueError(f'Operation "{operation}" requires update_args to be set')

        apply_decorators(
            bind_function_name(func, func_name),
            inject,
            require_auth(None),
            with_error_handler,
            method(endpoint),
        )

    return blueprint
