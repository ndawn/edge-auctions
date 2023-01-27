from flask.blueprints import Blueprint
from webargs.flaskparser import parser

from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.serializers.shop import ShopInstallSerializer
from auctions.services.shop_service import ShopService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = Blueprint("shop", __name__, url_prefix="/shop")


@blueprint.post("/install")
@with_error_handler
@login_required()
@inject
def install_shop(
    shop_service: ShopService = Provide(),
    shop_install_serializer: ShopInstallSerializer = Provide(),
) -> JsonResponse:
    args = parser.parse(shop_install_serializer, location="query")

    shop_id = args.get("shop_id")
    shop_url = args.get("shop_url")
    token = args.get("token")

    shop_service.install_shop(shop_id=shop_id, shop_name=shop_url, token=token)
    return JsonResponse({"ok": True})
