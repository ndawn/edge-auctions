from flask import Blueprint
from webargs.flaskparser import parser

from auctions.db.models.users import User
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.serializers.auctions import AuctionSerializer
from auctions.serializers.auctions import BriefAuctionSerializer
from auctions.serializers.auctions import WonAuctionPackSerializer
from auctions.serializers.bids import CreateBidSerializer
from auctions.serializers.ok import OkSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = Blueprint("auctions", __name__, url_prefix="/auctions")


@blueprint.get("/my")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def get_own_auctions(
    user: User,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.get_own_auctions(user)
    return JsonResponse(auction_serializer.dump(auction, many=True))


@blueprint.get("/won")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def get_won_auctions(
    user: User,
    auctions_service: AuctionsService = Provide(),
    won_auction_pack_serializer: WonAuctionPackSerializer = Provide(),
) -> JsonResponse:
    packs = auctions_service.get_won_auctions(user)
    return JsonResponse(won_auction_pack_serializer.dump(packs, many=True))


@blueprint.get("")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def list_active_auctions(
    user: User,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auctions = auctions_service.get_active_auctions(user)
    return JsonResponse(auction_serializer.dump(auctions, many=True))


@blueprint.get("/<int:id_>")
@with_error_handler
@login_required(inject_user=True)
@inject
def get_auction(
    id_: int,
    user: User,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.get_auction(id_, user)
    return JsonResponse(auction_serializer.dump(auction))


@blueprint.get("/<int:id_>/brief")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def get_auction_brief(
    id_: int,
    user: User,
    auctions_service: AuctionsService = Provide(),
    brief_auction_serializer: BriefAuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.get_auction(id_, user)
    return JsonResponse(brief_auction_serializer.dump(auction))


@blueprint.post("/<int:id_>/close")
@with_error_handler
@login_required()
@inject
def close_auction(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.close_auction(id_)
    return JsonResponse(auction_serializer.dump(auction))


@blueprint.delete("/<int:id_>")
@with_error_handler
@login_required()
@inject
def delete_auction(
    id_: int,
    auctions_repository: AuctionsRepository = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_repository.get_one_by_id(id_)
    auctions_repository.delete([auction])
    return JsonResponse(ok_serializer.dump(None))


@blueprint.post("/<int:id_>/bids")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def create_bid(
    id_: int,
    user: User,
    auctions_service: AuctionsService = Provide(),
    auctions_repository: AuctionsRepository = Provide(),
    create_bid_serializer: CreateBidSerializer = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    args = parser.parse(create_bid_serializer)
    auction = auctions_repository.get_one_by_id(id_)
    auctions_service.create_bid(auction, user, args["value"])
    return JsonResponse(ok_serializer.dump(None))
