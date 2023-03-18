import json
from traceback import print_exception

from flask import Blueprint
from flask import Response
from flask import request

from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.exceptions import NotAuthorizedError
from auctions.serializers.auth import ShopLoginRequestSerializer
from auctions.serializers.users import BriefUserSerializer
from auctions.serializers.users import UserSerializer
from auctions.services.auth_service import AuthService
from auctions.utils.endpoints import endpoint
from auctions.utils.response import JsonResponse

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@endpoint(blueprint.get("/me"), is_admin=False, inject_user=True)
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


@endpoint(blueprint.post("/login/shop"), protected=False)
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
