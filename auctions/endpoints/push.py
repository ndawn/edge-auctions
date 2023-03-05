from flask import Blueprint
from flask import Response
from webargs.flaskparser import parser

from auctions.config import Config
from auctions.db.models.users import User
from auctions.dependencies import inject
from auctions.dependencies import Provide
from auctions.serializers.ok import OkSerializer
from auctions.serializers.push import PushSubscriptionInfoSerializer
from auctions.services.push_service import PushService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = Blueprint("push", __name__, url_prefix="/push")


@blueprint.get("/key")
@with_error_handler
@login_required(is_admin=False)
@inject
def get_public_key(
    push_service: PushService = Provide(),
) -> JsonResponse:
    public_key = push_service.get_public_key()
    return JsonResponse({"key": public_key})


@blueprint.post("/subscribe")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def subscribe_to_updates(
    user: User,
    push_service: PushService = Provide(),
    push_subscription_info_serializer: PushSubscriptionInfoSerializer = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    subscription_info = parser.parse(push_subscription_info_serializer)
    push_service.subscribe(user, subscription_info)
    return JsonResponse(ok_serializer.dump(None))
