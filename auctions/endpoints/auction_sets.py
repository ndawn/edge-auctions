import base64

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
    operations=("read",),
    protected=("read",),
)


@blueprint.get("/active")
@with_error_handler
@login_required()
@inject
def search_active_auction_set(
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.get_active_auction_set()
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.get("/archived")
@with_error_handler
@login_required()
@inject
def list_archived_auction_sets(
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_sets = auctions_service.list_archived_auction_sets()
    return JsonResponse(auction_set_serializer.dump(auction_sets, many=True))


@blueprint.post("/")
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


@blueprint.post("/<int:id_>/start")
@with_error_handler
@login_required()
@inject
def start_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.start_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@blueprint.post("/<int:id_>/close")
@with_error_handler
@login_required()
@inject
def close_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.close_auction_set(id_)
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
    delete_object_serializer: DeleteObjectSerializer = Provide(),
) -> JsonResponse:
    auctions_service.delete_auction_set(id_)
    return JsonResponse(delete_object_serializer.dump(None))
