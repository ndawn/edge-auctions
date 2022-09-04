from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.items import Item
from auctions.dependencies import inject
from auctions.dependencies import Provide
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.delete_object import DeleteObjectSerializer
from auctions.serializers.items import ItemFilterRequestSerializer
from auctions.serializers.items import ItemIdsSerializer
from auctions.serializers.items import ItemSerializer
from auctions.services.items_service import ItemsService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=Item,
    serializer_name="item_serializer",
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    create_args=ItemSerializer(),
    update_args=ItemSerializer(partial=True),
    operations=("read",),
)


@blueprint.get("")
@with_error_handler
@login_required()
@inject
def list_items(
    items_service: ItemsService = Provide["items_service"],
    item_filter_request_serializer: ItemFilterRequestSerializer = Provide["item_filter_request_serializer"],
    item_serializer: ItemSerializer = Provide["item_serializer"],
) -> JsonResponse:
    args = parser.parse(item_filter_request_serializer, request, location="query")
    result = items_service.list_items(args)
    return JsonResponse(item_serializer.dump(result, many=True))


@blueprint.put("/<int:id_>")
@with_error_handler
@login_required()
@inject
def update_item(
    id_: int,
    items_service: ItemsService = Provide["items_service"],
    item_serializer: ItemSerializer = Provide["item_serializer"],
) -> JsonResponse:
    args = parser.parse(ItemSerializer(partial=True), request)
    item = items_service.update_item(id_, args)
    return JsonResponse(item_serializer.dump(item))


@blueprint.delete("")
@with_error_handler
@login_required()
@inject
def delete_items(
    items_service: ItemsService = Provide["items_service"],
    item_ids_serializer: ItemIdsSerializer = Provide["item_ids_serializer"],
    delete_object_serializer: DeleteObjectSerializer = Provide["delete_object_serializer"],
) -> JsonResponse:
    args = parser.parse(item_ids_serializer, request)
    items_service.delete_items(args.get("item_ids"))
    return JsonResponse(delete_object_serializer.dump(None))
