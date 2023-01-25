import inspect
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar


# DEPENDENCIES: dict[str, dict[str, ...]] = {
#     "config": {"class_": "auctions.config.Config"},
#     "oauth": {"class_": "authlib.integrations.flask_client.OAuth"},
#     "password_hasher": {"class_": "argon2.PasswordHasher"},
#     "task_queue": {"class_": "dramatiq.dramatiq"},
#     "users_service": {
#         "class_": "auctions.services.users_service.UsersService",
#         "depends": [
#             "password_service",
#             "auth_tokens_repository",
#             "users_repository",
#             "config",
#         ],
#     },
#     "auth_service": {
#         "class_": "auctions.services.auth_service.AuthService",
#         "depends": ["users_repository", "oauth", "config"],
#     },
#     "crud_service": {
#         "class_": "auctions.services.crud_service.CRUDServiceProvider",
#         "depends": [
#             "auction_sets_repository",
#             "auctions_repository",
#             "bids_repository",
#             "images_repository",
#             "item_types_repository",
#             "items_repository",
#             "price_categories_repository",
#             "supply_sessions_repository",
#             "templates_repository",
#             "auth_tokens_repository",
#             "users_repository",
#         ],
#     },
#     "images_service": {
#         "class_": "auctions.services.images_service.ImagesService",
#         "depends": ["images_repository", "config"],
#     },
#     "items_service": {
#         "class_": "auctions.services.items_service.ItemsService",
#         "depends": ["items_repository", "item_types_repository", "config"],
#     },
#     "supply_service": {
#         "class_": "auctions.services.supply_service.SupplyService",
#         "depends": [
#             "images_service",
#             "parse_service",
#             "images_repository",
#             "item_types_repository",
#             "items_repository",
#             "supply_sessions_repository",
#         ],
#     },
#     "parse_service": {
#         "class_": "auctions.services.parse_service.ParseService",
#         "depends": [
#             "images_service",
#             "item_types_repository",
#             "price_categories_repository",
#         ],
#     },
#     "auctions_service": {
#         "class_": "auctions.services.auctions_service.AuctionsService",
#         "depends": [
#             "crud_service",
#             "vk_notification_service",
#             "auction_sets_repository",
#             "auctions_repository",
#             "bids_repository",
#             "items_repository",
#             "users_repository",
#             "config",
#         ],
#     },
#     "export_service": {
#         "class_": "auctions.services.export_service.ExportService",
#         "depends": ["auctions_repository", "bidders_repository"],
#     },
#     "shop_service": {
#         "class_": "auctions.services.shop_service.ShopService",
#         "depends": ["password_service", "shop_info_repository", "config"],
#     },
#     "password_service": {
#         "class_": "auctions.services.password_service.PasswordService",
#         "depends": ["password_hasher", "config"],
#     },
#     "auction_sets_repository": {
#         "class_": "auctions.db.repositories.auction_sets.AuctionSetsRepository",
#         "depends": ["config"],
#     },
#     "auctions_repository": {
#         "class_": "auctions.db.repositories.auctions.AuctionsRepository",
#         "depends": ["config"],
#     },
#     "bids_repository": {
#         "class_": "auctions.db.repositories.bids.BidsRepository",
#         "depends": ["config"],
#     },
#     "images_repository": {
#         "class_": "auctions.db.repositories.images.ImagesRepository",
#         "depends": ["config"],
#     },
#     "item_types_repository": {
#         "class_": "auctions.db.repositories.item_types.ItemTypesRepository",
#         "depends": ["config"],
#     },
#     "items_repository": {
#         "class_": "auctions.db.repositories.items.ItemsRepository",
#         "depends": ["config"],
#     },
#     "price_categories_repository": {
#         "class_": "auctions.db.repositories.price_categories.PriceCategoriesRepository",
#         "depends": ["config"],
#     },
#     "shop_info_repository": {
#         "class_": "auctions.db.repositories.shop.ShopInfoRepository",
#         "depends": ["config"],
#     },
#     "supply_sessions_repository": {
#         "class_": "auctions.db.repositories.sessions.SupplySessionsRepository",
#         "depends": ["config"],
#     },
#     "templates_repository": {
#         "class_": "auctions.db.repositories.templates.TemplatesRepository",
#         "depends": ["config"],
#     },
#     "auth_tokens_repository": {
#         "class_": "auctions.db.repositories.users.AuthTokensRepository",
#         "depends": ["config"],
#     },
#     "users_repository": {
#         "class_": "auctions.db.repositories.users.UsersRepository",
#         "depends": ["config"],
#     },
#     "auction_set_serializer": {"class_": "auctions.serializers.auction_sets.AuctionSetSerializer"},
#     "auction_serializer": {"class_": "auctions.serializers.auctions.AuctionSerializer"},
#     "bid_serializer": {"class_": "auctions.serializers.bids.BidSerializer"},
#     "create_bid_serializer": {"class_": "auctions.serializers.bids.CreateBidSerializer"},
#     "exception_serializer": {"class_": "auctions.serializers.exceptions.ExceptionSerializer"},
#     "image_serializer": {"class_": "auctions.serializers.images.ImageSerializer"},
#     "item_counters_serializer": {"class_": "auctions.serializers.items.ItemCountersSerializer"},
#     "item_filter_request_serializer": {"class_": "auctions.serializers.items.ItemFilterRequestSerializer"},
#     "item_filtered_result_serializer": {"class_": "auctions.serializers.items.ItemFilteredResultSerializer"},
#     "item_ids_serializer": {"class_": "auctions.serializers.items.ItemIdsSerializer"},
#     "item_serializer": {"class_": "auctions.serializers.items.ItemSerializer"},
#     "item_type_serializer": {"class_": "auctions.serializers.item_types.ItemTypeSerializer"},
#     "price_category_serializer": {"class_": "auctions.serializers.price_categories.PriceCategorySerializer"},
#     "shop_install_serializer": {"class_": "auctions.serializers.shop.ShopInstallSerializer"},
#     "supply_session_serializer": {"class_": "auctions.serializers.sessions.SupplySessionSerializer"},
#     "template_serializer": {"class_": "auctions.serializers.templates.TemplateSerializer"},
#     "auth_token_serializer": {"class_": "auctions.serializers.users.AuthTokenSerializer"},
#     "user_serializer": {"class_": "auctions.serializers.users.UserSerializer"},
#     "auction_set_create_serializer": {"class_": "auctions.serializers.auction_sets.AuctionSetCreateSerializer"},
#     "delete_object_serializer": {"class_": "auctions.serializers.delete_object.DeleteObjectSerializer"},
# }
#
# ProvideOption = TypeVar(
#     "ProvideOption",
#     bound=Literal[
#         "config",
#         "users_service",
#         "auth_service",
#         "crud_service",
#         "images_service",
#         "items_service",
#         "supply_service",
#         "parse_service",
#         "auctions_service",
#         "export_service",
#         "shop_service",
#         "password_service",
#         "auction_sets_repository",
#         "auctions_repository",
#         "bids_repository",
#         "images_repository",
#         "item_types_repository",
#         "items_repository",
#         "price_categories_repository",
#         "supply_sessions_repository",
#         "templates_repository",
#         "auth_tokens_repository",
#         "users_repository",
#         "auction_set_serializer",
#         "auction_serializer",
#         "bid_serializer",
#         "create_bid_serializer",
#         "exception_serializer",
#         "image_serializer",
#         "item_counters_serializer",
#         "item_filter_request_serializer",
#         "item_filtered_result_serializer",
#         "item_ids_serializer",
#         "item_serializer",
#         "item_type_serializer",
#         "price_category_serializer",
#         "shop_install_serializer",
#         "supply_session_serializer",
#         "template_serializer",
#         "auth_token_serializer",
#         "user_serializer",
#         "auction_set_create_serializer",
#         "delete_object_serializer",
#     ],
# )


GLOBALS = {}


@dataclass
class Dependency:
    arg_name: str
    class_name: str
    class_: type
    depends: list["Dependency"]


class Provide:
    ...


Injectable = TypeVar("Injectable", bound=type)


class DependencyProvider:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._cache = {}

    @staticmethod
    def add_global(name: str, obj: ...) -> None:
        GLOBALS[name] = (obj, set())

    @staticmethod
    def get_qual_name(cls: type) -> str:
        if cls.__module__ == "builtins":
            return cls.__qualname__

        return f"{cls.__module__}.{cls.__qualname__}"

    def resolve_dependency_tree(self, func_or_cls: callable) -> list[Dependency]:
        signature = inspect.signature(func_or_cls)

        return [
            Dependency(
                arg_name=arg_name,
                class_name=self.get_qual_name(arg_value.annotation),
                class_=arg_value.annotation,
                depends=self.resolve_dependency_tree(arg_value.annotation),
            )
            for arg_name, arg_value in signature.parameters.items()
            if (
                isinstance(arg_value.default, (Provide, inspect.Parameter.empty))
                and not isinstance(arg_value.annotation, inspect.Parameter.empty)
                and "__injectable__" in arg_value.annotation.__dict__
            )
        ]

    def provide(self, dependency: Dependency) -> object:
        if dependency.class_name in GLOBALS:
            return GLOBALS[dependency.class_name]

        if dependency.class_name in self._cache:
            return self._cache[dependency.class_name]

        dep_kwargs = {}

        for sub_dependency in dependency.depends:
            dep_instance = self.provide(sub_dependency)
            dep_kwargs[dependency.arg_name] = dep_instance
            self._cache[dependency.class_name] = dep_instance

        return dependency.class_(**dep_kwargs)

    def invalidate_cache(self, dependency: Dependency) -> None:
        if dependency.class_name in self._cache:
            del self._cache[dependency.class_name]

        for sub_dependency in dependency.depends:
            self.invalidate_cache(sub_dependency)


provider = DependencyProvider()


def inject(func: callable) -> callable:
    dependency_tree = provider.resolve_dependency_tree(func)

    @wraps(func)
    def decorated(*args, **kwargs):
        dep_kwargs = {}

        for dependency in dependency_tree:
            dep_kwargs[dependency.arg_name] = provider.provide(dependency)

        result = func(*args, **kwargs, **dep_kwargs)

        for dependency in dependency_tree:
            provider.invalidate_cache(dependency)

        return result

    return decorated


def injectable(cls: Injectable) -> Injectable:
    cls.__injectable__ = True
    return cls
