from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.auction_sets import AuctionSet
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auction_sets import AuctionSetCreateSerializer
from auctions.serializers.auction_sets import AuctionSetSerializer
from auctions.serializers.delete_object import DeleteObjectSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=AuctionSet,
    serializer_name="auction_set_serializer",
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    operations=("read",),
    protected=("read",),
)


@blueprint.get("/active")
@with_error_handler
@login_required(is_admin=False)
@inject
def search_active_auction_set(
    auctions_service: AuctionsService = Provide["auctions_service"],
    auction_set_serializer: AuctionSetSerializer = Provide["auction_set_serializer"],
) -> JsonResponse:
    args = parser.parse({
        "target_id": fields.Int(data_key="targetId"),
    }, request, location="query")
    auction_set = auctions_service.get_active_auction_set(args["target_id"])
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.get("/archived")
@with_error_handler
@login_required(is_admin=False)
@inject
def list_archived_auction_sets(
    auctions_service: AuctionsService = Provide["auctions_service"],
    auction_set_serializer: AuctionSetSerializer = Provide["auction_set_serializer"],
) -> JsonResponse:
    args = parser.parse({
        "target_id": fields.Int(required=True, data_key="targetId"),
    }, request, location="query")
    auction_sets = auctions_service.list_archived_auction_sets(args["target_id"])
    return JsonResponse(auction_set_serializer.dump(auction_sets, many=True))


@blueprint.post("/")
@with_error_handler
@login_required()
@inject
def create_auction_set(
    auctions_service: AuctionsService = Provide["auctions_service"],
    auction_set_create_serializer: AuctionSetCreateSerializer = Provide["auction_set_create_serializer"],
    auction_set_serializer: AuctionSetSerializer = Provide["auction_set_serializer"],
) -> JsonResponse:
    args = parser.parse(auction_set_create_serializer, request)
    auction_set = auctions_service.create_auction_set(
        target_id=args["target_id"],
        date_due=args["date_due"],
        anti_sniper=args["anti_sniper"],
        item_ids=args["item_ids"],
    )
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.post("/<int:id_>/start")
@with_error_handler
@login_required()
@inject
def start_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide["auctions_service"],
    auction_set_serializer: AuctionSetSerializer = Provide["auction_set_serializer"],
) -> JsonResponse:
    auction_set = auctions_service.start_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.post("/<int:id_>/close")
@with_error_handler
@login_required()
@inject
def close_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide["auctions_service"],
    auction_set_serializer: AuctionSetSerializer = Provide["auction_set_serializer"],
) -> JsonResponse:
    auction_set = auctions_service.close_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.delete("/<int:id_>")
@with_error_handler
@login_required()
@inject
def delete_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide["auctions_service"],
    delete_object_serializer: DeleteObjectSerializer = Provide["delete_object_serializer"],
) -> JsonResponse:
    auctions_service.delete_auction_set(id_)
    return JsonResponse(delete_object_serializer.dump(None))
