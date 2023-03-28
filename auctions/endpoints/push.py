from flask import Blueprint
from webargs.flaskparser import parser

from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.serializers.ok import OkSerializer
from auctions.serializers.push import PushSubscriptionInfoSerializer
from auctions.services.push_service import PushService
from auctions.utils.endpoints import endpoint
from auctions.utils.response import JsonResponse

blueprint = Blueprint("push", __name__, url_prefix="/push")


@endpoint(blueprint.post("/subscribe"), is_admin=False, inject_user=True)
def subscribe_to_updates(
    user: User,
    push_service: PushService = Provide(),
    push_subscription_info_serializer: PushSubscriptionInfoSerializer = Provide(),
    ok_serializer: OkSerializer = Provide(),
) -> JsonResponse:
    subscription_info = parser.parse(push_subscription_info_serializer)
    push_service.subscribe(user, subscription_info)
    return JsonResponse(ok_serializer.dump(None))
