from traceback import print_exception

from flask import Blueprint
from flask import Response
from flask import request
from webargs.flaskparser import parser

from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.serializers.vk import VKCallbackMessageSerializer
from auctions.services.vk_callback_service import VKCallbackService

blueprint = Blueprint("vk", __name__, url_prefix="/vk")


@blueprint.get("")
@inject
def handle_vk_callback_message(
    vk_callback_service: VKCallbackService = Provide["vk_callback_service"],
    vk_callback_message_serializer: VKCallbackMessageSerializer = Provide["vk_callback_message_serializer"],
) -> Response:
    try:
        args = parser.parse(vk_callback_message_serializer, request)
        return vk_callback_service.handle_callback_message(args)
    except Exception as exception:
        print_exception(exception.__class__, exception, exception.__traceback__)
        return Response("ok")
