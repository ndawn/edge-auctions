from flask.blueprints import Blueprint
from webargs.flaskparser import parser

from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.serializers.users import AuthTokenSerializer
from auctions.serializers.users import UserSerializer
from auctions.services.users_service import UsersService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = Blueprint("accounts", __name__, url_prefix="/accounts")


@blueprint.get("/me")
@with_error_handler
@login_required(inject_user=True)
@inject
def me(*, user: User, user_serializer: UserSerializer = Provide["user_serializer"]) -> JsonResponse:
    return JsonResponse(user_serializer.dump(user))


@blueprint.post("/login")
@with_error_handler
@inject
def login(
    users_service: UsersService = Provide["users_service"],
    auth_token_serializer: AuthTokenSerializer = Provide["auth_token_serializer"],
) -> JsonResponse:
    args = parser.parse(UserSerializer(only=("username", "password")))

    username = args.get("username")
    password = args.get("password")

    auth_token = users_service.login_user(
        username=username,
        password=password,
    )

    return JsonResponse(auth_token_serializer.dump(auth_token))


@blueprint.post("/register")
@with_error_handler
@inject
def register(
    users_service: UsersService = Provide["users_service"],
    auth_token_serializer: AuthTokenSerializer = Provide["auth_token_serializer"],
) -> JsonResponse:
    args = parser.parse(UserSerializer())

    username = args.get("username")
    password = args.get("password")
    first_name = args.get("first_name")
    last_name = args.get("last_name")

    users_service.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    auth_token = users_service.login_user(username=username, password=password)
    return JsonResponse(auth_token_serializer.dump(auth_token), status=201)
