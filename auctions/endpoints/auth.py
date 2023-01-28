from flask import Blueprint
from webargs.flaskparser import parser

from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.services.auth_service import AuthService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.response import JsonResponse

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.post("/login/callback")
@with_error_handler
@inject
def login_callback(
    auth_service: UserService = Provide(),
    auction_serializer: AuctionSerializer = Provide(),
) -> JsonResponse:
    auction = auctions_service.close_auction(id_)
    return JsonResponse(auction_serializer.dump(auction))
