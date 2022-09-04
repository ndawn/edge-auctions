from auctions.db.models.auctions import Auction
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auctions import AuctionSerializer
from auctions.serializers.delete_object import DeleteObjectSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=Auction,
    serializer_name="auction_serializer",
    operations=("read",),
)


@blueprint.post("/<int:id_>/close")
@with_error_handler
@login_required()
@inject
def close_auction(
    id_: int,
    auctions_service: AuctionsService = Provide["auctions_service"],
    auction_serializer: AuctionSerializer = Provide["auction_serializer"],
) -> JsonResponse:
    auction = auctions_service.close_auction(id_)
    return JsonResponse(auction_serializer.dump(auction))


@blueprint.delete("/<int:id_>")
@with_error_handler
@login_required()
@inject
def delete_auction(
    id_: int,
    auctions_repository: AuctionsRepository = Provide["auctions_repository"],
    delete_object_serializer: DeleteObjectSerializer = Provide["delete_object_serializer"],
) -> JsonResponse:
    auction = auctions_repository.get_one_by_id(id_)
    auctions_repository.delete([auction])
    return JsonResponse(delete_object_serializer.dump(None))
