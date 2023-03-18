from flask import Blueprint
from webargs.flaskparser import parser

from auctions.db.models.users import User
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.dependencies import Provide
from auctions.serializers.auctions import AuctionSerializer
from auctions.serializers.auctions import BriefAuctionSerializer
from auctions.serializers.auctions import WonAuctionPackSerializer
from auctions.serializers.bids import CreateBidSerializer
from auctions.serializers.ok import OkSerializer
from auctions.services.auctions_service import AuctionsService
from auctions.utils.endpoints import endpoint
from auctions.utils.response import JsonResponse

blueprint = Blueprint("auctions", __name__, url_prefix="/auctions")


@endpoint(blueprint.get("/my"), is_admin=False, inject_user=True)
def get_own_auctions(
    user: User,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.get_own_auctions(user)
    return JsonResponse(auction_serializer.dump(auction, many=True))


@endpoint(blueprint.get("/won"), is_admin=False, inject_user=True)
def get_won_auctions(
    user: User,
    auctions_service: AuctionsService = Provide(),
    won_auction_pack_serializer: WonAuctionPackSerializer = Provide(),
) -> JsonResponse:
    packs = auctions_service.get_won_auctions(user)
    return JsonResponse(won_auction_pack_serializer.dump(packs, many=True))


@endpoint(blueprint.get(""), is_admin=False, inject_user=True)
def list_active_auctions(
    user: User,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auctions = auctions_service.get_active_auctions(user)
    return JsonResponse(auction_serializer.dump(auctions, many=True))


@endpoint(blueprint.get("/<int:id_>"), inject_user=True)
def get_auction(
    id_: int,
    user: User,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.get_auction(id_, user)
    return JsonResponse(auction_serializer.dump(auction))


@endpoint(blueprint.get("/<int:id_>/brief"), is_admin=False, inject_user=True)
def get_auction_brief(
    id_: int,
    user: User,
    auctions_service: AuctionsService = Provide(),
    brief_auction_serializer: BriefAuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.get_auction(id_, user)
    return JsonResponse(brief_auction_serializer.dump(auction))


@endpoint(blueprint.post("/<int:id_>/close"))
def close_auction(
    id_: int,
    auctions_service: AuctionsService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.close_auction(id_)
    return JsonResponse(auction_serializer.dump(auction))


@endpoint(blueprint.delete("/<int:id_>"))
def delete_auction(
    id_: int,
    auctions_repository: AuctionsRepository = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_repository.get_one_by_id(id_)
    auctions_repository.delete([auction])
    return JsonResponse(ok_serializer.dump(None))


@endpoint(blueprint.post("/<int:id_>/bids"), is_admin=False, inject_user=True)
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
