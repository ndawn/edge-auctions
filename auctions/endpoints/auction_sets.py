import base64

from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auction_sets import AuctionSetCreateSerializer
from auctions.serializers.auction_sets import AuctionSetSerializer
from auctions.serializers.auction_sets import BriefAuctionSetSerializer
from auctions.serializers.ok import OkSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.services.export_service import ExportService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=AuctionSet,
    serializer_class=AuctionSetSerializer,
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    operations=("list", "read"),
    protected=("list", "read"),
)


@blueprint.post("")
@with_error_handler
@login_required()
@inject
def create_auction_set(
    auctions_service: AuctionsService = Provide(),
    auction_set_create_serializer: AuctionSetCreateSerializer = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    args = parser.parse(auction_set_create_serializer, request)
    auction_set = auctions_service.create_auction_set(
        date_due=args["date_due"],
        anti_sniper=args["anti_sniper"],
        item_ids=args["item_ids"],
    )
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.post("/<int:id_>/publish")
@with_error_handler
@login_required()
@inject
def publish_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.publish_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.post("/<int:id_>/unpublish")
@with_error_handler
@login_required()
@inject
def unpublish_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.unpublish_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.post("/<int:id_>/export/empty")
@with_error_handler
@login_required()
@inject
def export_empty_auctions(id_: int, export_service: ExportService = Provide()) -> JsonResponse:
    export_result = export_service.export_empty_auctions(id_)
    export_encoded = base64.b64encode(export_result)
    return JsonResponse({"result": export_encoded.decode("utf-8")})


@blueprint.delete("/<int:id_>")
@with_error_handler
@login_required()
@inject
def delete_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    auctions_service.delete_auction_set(id_)
    return JsonResponse(ok_serializer.dump(None))
