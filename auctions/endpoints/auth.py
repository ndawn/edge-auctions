import json
from traceback import print_exception
from urllib.parse import urlencode

from flask import Blueprint
from flask import Response
from flask import redirect
from flask import request
from webargs.flaskparser import parser

from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.exceptions import NotAuthorizedError
from auctions.serializers.auth import Auth0LoginRequestSerializer
from auctions.serializers.auth import ShopLoginRequestSerializer
from auctions.serializers.users import BriefUserSerializer
from auctions.serializers.users import UserSerializer
from auctions.services.auth_service import AuthService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.get("/me")
@with_error_handler
@login_required(is_admin=False, inject_user=True)
@inject
def get_me(
    user: User,
    user_serializer: UserSerializer = Provide(),
    brief_user_serializer: BriefUserSerializer = Provide(),
) -> JsonResponse:
    if user.is_admin:
        return JsonResponse(user_serializer.dump(user))
    else:
        return JsonResponse(brief_user_serializer.dump(user))


# @blueprint.get("/login")
# @with_error_handler
# @inject
# def login_callback(
#     auth_service: AuthService = Provide(),
#     auth0_login_request_serializer: Auth0LoginRequestSerializer = Provide(),
# ) -> Response:
#     args = parser.parse(auth0_login_request_serializer, location="query")
#     reply_token, redirect_uri = auth_service.login_from_auth0(args)
#
#     query_string = urlencode({"state": args["state"], "token": reply_token})
#     redirect_to = f"{redirect_uri}?{query_string}"
#
#     return redirect(redirect_to, code=307)


@blueprint.post("/login/shop")
@with_error_handler
@inject
def login_from_shop(
    auth_service: AuthService = Provide(),
    shop_login_request_serializer: ShopLoginRequestSerializer = Provide(),
    brief_user_serializer: BriefUserSerializer = Provide(),
) -> Response:
    try:
        body = json.loads(request.data.decode("utf-8"))
        args = shop_login_request_serializer.load(body)
    except Exception as exception:
        print_exception(type(exception), exception, exception.__traceback__)
        raise NotAuthorizedError("Invalid request") from exception

    user, id_token, access_token = auth_service.login_from_shop(args)
    user.access_token = access_token
    user.id_token = id_token

    return JsonResponse(brief_user_serializer.dump(user))
