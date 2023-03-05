from flask import request
from flask.blueprints import Blueprint
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.images import Image
from auctions.db.repositories.images import ImagesRepository
from auctions.db.repositories.item_types import ItemTypesRepository
from auctions.db.repositories.items import ItemsRepository
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.exceptions import ObjectDoesNotExist
from auctions.exceptions import SessionStartFailed
from auctions.serializers.items import ItemJoinData
from auctions.serializers.items import ItemSerializer
from auctions.serializers.ok import OkSerializer
from auctions.serializers.sessions import SupplySessionSerializer
from auctions.services.supply_service import SupplyService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = Blueprint("supply", __name__, url_prefix="/supply")


@blueprint.get("/current")
@with_error_handler
@login_required()
@inject
def get_current_session(
    supply_service: SupplyService = Provide(),
    supply_session_serializer: SupplySessionSerializer = Provide(),
) -> JsonResponse:
    session = supply_service.get_current_session()
    return JsonResponse(supply_session_serializer.dump(session))


@blueprint.post("/start")
@with_error_handler
@login_required()
@inject
def start_session(
    item_types_repository: ItemTypesRepository = Provide(),
    images_repository: ImagesRepository = Provide(),
    supply_service: SupplyService = Provide(),
    supply_session_serializer: SupplySessionSerializer = Provide(),
) -> JsonResponse:
    args = parser.parse(
        {
            "item_type_id": fields.Int(required=True, data_key="itemTypeId"),
            "image_ids": fields.List(fields.Int(), required=True, data_key="imageIds"),
        },
        request,
    )

    try:
        supply_service.get_current_session()
        raise SessionStartFailed("Cannot start a session while there is already one in progress")
    except ObjectDoesNotExist:
        pass

    item_type = item_types_repository.get_one_by_id(args["item_type_id"])
    images = images_repository.get_many(ids=args["image_ids"])

    session = supply_service.start_session(item_type=item_type, images=images)
    return JsonResponse(supply_session_serializer.dump(session))


@blueprint.post("/current/<int:id_>/process")
@with_error_handler
@login_required()
@inject
def process_item(
    id_: int,
    items_repository: ItemsRepository = Provide(),
    supply_service: SupplyService = Provide(),
    item_serializer: ItemSerializer = Provide(),
) -> JsonResponse:
    item = items_repository.get_one_by_id(id_)
    item = supply_service.process_item(item)
    return JsonResponse(item_serializer.dump(item))


@blueprint.post("/current/add")
@with_error_handler
@login_required()
@inject
def add_images(
    images_repository: ImagesRepository = Provide(),
    supply_service: SupplyService = Provide(),
    supply_session_serializer: SupplySessionSerializer = Provide(),
) -> JsonResponse:
    args = parser.parse(
        {
            "image_ids": fields.List(fields.Int(), required=True, data_key="imageIds"),
        },
        request,
    )

    session = supply_service.get_current_session()
    images = images_repository.get_many(Image.id.in_(args["image_ids"]))
    supply_service.add_images(session, images)
    return JsonResponse(supply_session_serializer.dump(session))


@blueprint.post("/current/join")
@with_error_handler
@login_required()
@inject
def join_items(
    images_repository: ImagesRepository = Provide(),
    items_repository: ItemsRepository = Provide(),
    supply_service: SupplyService = Provide(),
    item_serializer: ItemSerializer = Provide(),
) -> JsonResponse:
    args = parser.parse(ItemJoinData(), request)
    item_to_keep = items_repository.get_one_by_id(args.get("item_to_keep_id"))
    item_to_drop = items_repository.get_one_by_id(args.get("item_to_drop_id"))
    images = images_repository.get_many(Image.id.in_(args.get("image_ids")))
    main_image = images_repository.get_one_by_id(args.get("main_image_id"))
    item = supply_service.join_items(item_to_keep, item_to_drop, images, main_image)
    return JsonResponse(item_serializer.dump(item))


@blueprint.post("/current/apply")
@with_error_handler
@login_required()
@inject
def apply_session(
    supply_service: SupplyService = Provide(),
    item_serializer: ItemSerializer = Provide(),
) -> JsonResponse:
    items = supply_service.apply_session()
    return JsonResponse(item_serializer.dump(items, many=True))


@blueprint.post("/current/discard")
@with_error_handler
@login_required()
@inject
def discard_session(
    supply_service: SupplyService = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    supply_service.discard_session()
    return JsonResponse(ok_serializer.dump(None))
