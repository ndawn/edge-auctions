from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.auction_sets import AuctionSet
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auction_sets import AuctionSetCreateSerializer
from auctions.serializers.auction_sets import AuctionSetSerializer
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
    operations=("list", "read", "delete"),
)


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
    auction_set = auctions_service.create_auction_set(args["target_id"], args["amounts"])
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
