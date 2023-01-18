from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.items import Item
from auctions.dependencies import inject
from auctions.dependencies import Provide
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.delete_object import DeleteObjectSerializer
from auctions.serializers.items import ItemCountersSerializer
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


@blueprint.get("/counters")
@with_error_handler
@login_required()
@inject
def get_item_counters(
    items_service: ItemsService = Provide["items_service"],
    item_counters_serializer: ItemCountersSerializer = Provide["item_counters_serializer"],
) -> JsonResponse:
    result = items_service.get_counters()
    return JsonResponse(item_counters_serializer.dump({"counters": result}))


@blueprint.post("/random_set")
@with_error_handler
@login_required()
@inject
def get_random_item_set_for_auction(
    items_service: ItemsService = Provide["items_service"],
    item_serializer: ItemSerializer = Provide["item_serializer"],
) -> JsonResponse:
    args = parser.parse({
        "amounts": fields.Dict(
            keys=fields.Int(),
            values=fields.Dict(keys=fields.Int(), values=fields.Int()),
            required=True,
        )
    }, request)
    result = items_service.get_random_set(args["amounts"])
    return JsonResponse(item_serializer.dump(result, many=True))


@blueprint.post("/random_auction")
@with_error_handler
@login_required()
@inject
def get_random_item_for_auction(
    items_service: ItemsService = Provide["items_service"],
    item_serializer: ItemSerializer = Provide["item_serializer"],
) -> JsonResponse:
    args = parser.parse({
        "item_type_id": fields.Int(data_key="itemTypeId"),
        "price_category_id": fields.Int(data_key="priceCategoryId"),
        "exclude_ids": fields.List(fields.Int(), data_key="excludeIds"),
    }, request)
    result = items_service.get_random_item_for_auction(
        args["item_type_id"],
        args["price_category_id"],
        args["exclude_ids"],
    )
    return JsonResponse(item_serializer.dump(result) if result is not None else None)


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
