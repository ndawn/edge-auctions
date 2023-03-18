import base64

from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.auction_sets import AuctionSet
from auctions.dependencies import Provide
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auction_sets import AuctionSetCreateSerializer
from auctions.serializers.auction_sets import AuctionSetSerializer
from auctions.serializers.ok import OkSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.services.export_service import ExportService
from auctions.utils.endpoints import endpoint
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=AuctionSet,
    serializer_class=AuctionSetSerializer,
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    operations={"list", "read"},
    protected={"list", "read"},
)


@endpoint(blueprint.post(""))
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


@endpoint(blueprint.post("/<int:id_>/publish"))
def publish_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.publish_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@endpoint(blueprint.post("/<int:id_>/unpublish"))
def unpublish_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_set_serializer: AuctionSetSerializer = Provide(),
) -> JsonResponse:
    auction_set = auctions_service.unpublish_auction_set(id_)
    return JsonResponse(auction_set_serializer.dump(auction_set))


@endpoint(blueprint.post("/<int:id_>/export/empty"))
def export_empty_auctions(id_: int, export_service: ExportService = Provide()) -> JsonResponse:
    export_result = export_service.export_empty_auctions(id_)
    export_encoded = base64.b64encode(export_result)
    return JsonResponse({"result": export_encoded.decode("utf-8")})


@endpoint(blueprint.delete("/<int:id_>"))
def delete_auction_set(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    auctions_service.delete_auction_set(id_)
    return JsonResponse(ok_serializer.dump(None))
