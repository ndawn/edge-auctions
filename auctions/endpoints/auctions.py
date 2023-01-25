from webargs.flaskparser import parser

from auctions.db.models.auctions import Auction
from auctions.db.models.users import User
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auctions import AuctionSerializer
from auctions.serializers.bids import CreateBidSerializer
from auctions.serializers.delete_object import DeleteObjectSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import require_auth
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=Auction,
    serializer_class=AuctionSerializer,
    operations=("read",),
    protected=(),
)


@blueprint.post("/<int:id_>/close")
@with_error_handler
@require_auth(None)
@inject
def close_auction(
    id_: int,
    auctions_service: AuctionsService,
    auction_serializer: AuctionSerializer,
) -> JsonResponse:
    auction = auctions_service.close_auction(id_)
    return JsonResponse(auction_serializer.dump(auction))


@blueprint.delete("/<int:id_>")
@with_error_handler
@require_auth(None)
@inject
def delete_auction(
    id_: int,
    auctions_repository: AuctionsRepository,
    delete_object_serializer: DeleteObjectSerializer,
) -> JsonResponse:
    auction = auctions_repository.get_one_by_id(id_)
    auctions_repository.delete([auction])
    return JsonResponse(delete_object_serializer.dump(None))


@blueprint.post("/<int:id_>/bids")
@with_error_handler
@require_auth(None)
@inject
def create_bid(
    id_: int,
    user: User,
    auctions_service: AuctionsService,
    auctions_repository: AuctionsRepository,
    create_bid_serializer: CreateBidSerializer,
    delete_object_serializer: DeleteObjectSerializer,
) -> JsonResponse:
    args = parser.parse(create_bid_serializer)

    auction = auctions_repository.get_one_by_id(id_)

    auctions_service.create_bid(auction, user.bidder, )
    return JsonResponse(delete_object_serializer.dump(None))
