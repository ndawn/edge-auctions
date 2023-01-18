import inspect
from functools import wraps
from importlib import import_module
from typing import Callable
from typing import Literal
from typing import Optional
from typing import TypedDict
from typing import TypeVar

from sqlalchemy.orm import Session

from auctions.db.session import SessionManager


class DependencyMapType(TypedDict):
    class_: str
    depends: Optional[list[str]]


DEPENDENCIES: dict[str, DependencyMapType] = {
    "config": {"class_": "auctions.config.Config"},
    "task_queue": {"class_": "dramatiq.dramatiq"},
    "users_service": {
        "class_": "auctions.services.users_service.UsersService",
        "depends": [
            "password_service",
            "auth_tokens_repository",
            "external_users_repository",
            "users_repository",
            "vk_request_service",
            "config",
        ],
    },
    "crud_service": {
        "class_": "auctions.services.crud_service.CRUDServiceProvider",
        "depends": [
            "auction_sets_repository",
            "auction_targets_repository",
            "auctions_repository",
            "bidders_repository",
            "bids_repository",
            "external_entities_repository",
            "external_tokens_repository",
            "external_users_repository",
            "images_repository",
            "item_types_repository",
            "items_repository",
            "price_categories_repository",
            "supply_sessions_repository",
            "templates_repository",
            "auth_tokens_repository",
            "users_repository",
        ],
    },
    "images_service": {
        "class_": "auctions.services.images_service.ImagesService",
        "depends": ["images_repository", "config"],
    },
    "items_service": {
        "class_": "auctions.services.items_service.ItemsService",
        "depends": ["items_repository", "item_types_repository", "config"],
    },
    "supply_service": {
        "class_": "auctions.services.supply_service.SupplyService",
        "depends": [
            "images_service",
            "parse_service",
            "images_repository",
            "item_types_repository",
            "items_repository",
            "supply_sessions_repository",
        ],
    },
    "parse_service": {
        "class_": "auctions.services.parse_service.ParseService",
        "depends": [
            "images_service",
            "item_types_repository",
            "price_categories_repository",
        ],
    },
    "auctions_service": {
        "class_": "auctions.services.auctions_service.AuctionsService",
        "depends": [
            "crud_service",
            "vk_notification_service",
            "auction_sets_repository",
            "auction_targets_repository",
            "auctions_repository",
            "bidders_repository",
            "bids_repository",
            "external_entities_repository",
            "items_repository",
            "config",
        ],
    },
    "vk_auctions_service": {
        "class_": "auctions.services.vk_auctions_service.VKAuctionsService",
        "depends": [
            "vk_request_service",
            "auction_sets_repository",
            "auctions_repository",
            "external_entities_repository",
        ],
    },
    "vk_callback_service": {
        "class_": "auctions.services.vk_callback_service.VKCallbackService",
        "depends": [
            "auctions_service",
            "vk_notification_service",
            "vk_request_service",
            "bidders_repository",
            "external_entities_repository",
            "external_tokens_repository",
            "config",
        ],
    },
    "vk_notification_service": {
        "class_": "auctions.services.vk_notification_service.VKNotificationService",
        "depends": ["vk_request_service", "config"],
    },
    "vk_request_service": {
        "class_": "auctions.services.vk_request_service.VKRequestService",
        "depends": ["external_tokens_repository", "config"],
    },
    "password_service": {"class_": "auctions.services.password_service.PasswordService"},
    "auction_sets_repository": {
        "class_": "auctions.db.repositories.auction_sets.AuctionSetsRepository",
        "depends": ["config"],
    },
    "auction_targets_repository": {
        "class_": "auctions.db.repositories.auction_targets.AuctionTargetsRepository",
        "depends": ["config"],
    },
    "auctions_repository": {
        "class_": "auctions.db.repositories.auctions.AuctionsRepository",
        "depends": ["config"],
    },
    "bidders_repository": {
        "class_": "auctions.db.repositories.bidders.BiddersRepository",
        "depends": ["config"],
    },
    "bids_repository": {
        "class_": "auctions.db.repositories.bids.BidsRepository",
        "depends": ["config"],
    },
    "external_entities_repository": {
        "class_": "auctions.db.repositories.external.ExternalEntitiesRepository",
        "depends": ["config"],
    },
    "external_tokens_repository": {
        "class_": "auctions.db.repositories.external.ExternalTokensRepository",
        "depends": ["config"],
    },
    "external_users_repository": {
        "class_": "auctions.db.repositories.users.ExternalUsersRepository",
        "depends": ["config"],
    },
    "images_repository": {
        "class_": "auctions.db.repositories.images.ImagesRepository",
        "depends": ["config"],
    },
    "item_types_repository": {
        "class_": "auctions.db.repositories.item_types.ItemTypesRepository",
        "depends": ["config"],
    },
    "items_repository": {
        "class_": "auctions.db.repositories.items.ItemsRepository",
        "depends": ["config"],
    },
    "price_categories_repository": {
        "class_": "auctions.db.repositories.price_categories.PriceCategoriesRepository",
        "depends": ["config"],
    },
    "supply_sessions_repository": {
        "class_": "auctions.db.repositories.sessions.SupplySessionsRepository",
        "depends": ["config"],
    },
    "templates_repository": {
        "class_": "auctions.db.repositories.templates.TemplatesRepository",
        "depends": ["config"],
    },
    "auth_tokens_repository": {
        "class_": "auctions.db.repositories.users.AuthTokensRepository",
        "depends": ["config"],
    },
    "users_repository": {
        "class_": "auctions.db.repositories.users.UsersRepository",
        "depends": ["config"],
    },
    "auction_set_serializer": {"class_": "auctions.serializers.auction_sets.AuctionSetSerializer"},
    "auction_target_serializer": {"class_": "auctions.serializers.auction_targets.AuctionTargetSerializer"},
    "auction_serializer": {"class_": "auctions.serializers.auctions.AuctionSerializer"},
    "bidder_serializer": {"class_": "auctions.serializers.bidders.BidderSerializer"},
    "bid_serializer": {"class_": "auctions.serializers.bids.BidSerializer"},
    "create_bid_serializer": {"class_": "auctions.serializers.bids.CreateBidSerializer"},
    "exception_serializer": {"class_": "auctions.serializers.exceptions.ExceptionSerializer"},
    "external_entity_serializer": {"class_": "auctions.serializers.external.ExternalEntitySerializer"},
    "external_token_serializer": {"class_": "auctions.serializers.external.ExternalTokenSerializer"},
    "external_user_serializer": {"class_": "auctions.serializers.users.ExternalUserSerializer"},
    "image_serializer": {"class_": "auctions.serializers.images.ImageSerializer"},
    "item_counters_serializer": {"class_": "auctions.serializers.items.ItemCountersSerializer"},
    "item_filter_request_serializer": {"class_": "auctions.serializers.items.ItemFilterRequestSerializer"},
    "item_filtered_result_serializer": {"class_": "auctions.serializers.items.ItemFilteredResultSerializer"},
    "item_ids_serializer": {"class_": "auctions.serializers.items.ItemIdsSerializer"},
    "item_serializer": {"class_": "auctions.serializers.items.ItemSerializer"},
    "item_type_serializer": {"class_": "auctions.serializers.item_types.ItemTypeSerializer"},
    "miniapp_login_serializer": {"class_": "auctions.serializers.miniapp.MiniappLoginSerializer"},
    "price_category_serializer": {"class_": "auctions.serializers.price_categories.PriceCategorySerializer"},
    "supply_session_serializer": {"class_": "auctions.serializers.sessions.SupplySessionSerializer"},
    "template_serializer": {"class_": "auctions.serializers.templates.TemplateSerializer"},
    "auth_token_serializer": {"class_": "auctions.serializers.users.AuthTokenSerializer"},
    "user_serializer": {"class_": "auctions.serializers.users.UserSerializer"},
    "auction_set_create_serializer": {"class_": "auctions.serializers.auction_sets.AuctionSetCreateSerializer"},
    "external_entity_create_serializer": {"class_": "auctions.serializers.external.ExternalEntityCreateSerializer"},
    "delete_object_serializer": {"class_": "auctions.serializers.delete_object.DeleteObjectSerializer"},
    "vk_callback_message_serializer": {"class_": "auctions.serializers.vk.VKCallbackMessageSerializer"},
}

ProvideOption = TypeVar(
    "ProvideOption",
    bound=Literal[
        "config",
        "users_service",
        "crud_service",
        "images_service",
        "items_service",
        "supply_service",
        "parse_service",
        "auctions_service",
        "vk_service",
        "vk_callback_service",
        "vk_notification_service",
        "vk_request_service",
        "password_service",
        "auction_sets_repository",
        "auction_targets_repository",
        "auctions_repository",
        "bidders_repository",
        "bids_repository",
        "external_entities_repository",
        "external_tokens_repository",
        "external_users_repository",
        "images_repository",
        "item_types_repository",
        "items_repository",
        "price_categories_repository",
        "supply_sessions_repository",
        "templates_repository",
        "auth_tokens_repository",
        "users_repository",
        "auction_set_serializer",
        "auction_target_serializer",
        "auction_serializer",
        "bidder_serializer",
        "bid_serializer",
        "create_bid_serializer",
        "exception_serializer",
        "external_entity_serializer",
        "external_token_serializer",
        "image_serializer",
        "item_counters_serializer",
        "item_filter_request_serializer",
        "item_filtered_result_serializer",
        "item_ids_serializer",
        "item_serializer",
        "item_type_serializer",
        "miniapp_login_serializer",
        "price_category_serializer",
        "supply_session_serializer",
        "template_serializer",
        "auth_token_serializer",
        "user_serializer",
        "auction_set_create_serializer",
        "external_entity_create_serializer",
        "delete_object_serializer",
        "vk_callback_message_serializer",
    ],
)


GLOBALS = {}


class Provide:
    def __init__(self, option: ProvideOption) -> None:
        self.option = option

    def __class_getitem__(cls, item: ProvideOption) -> "Provide":
        return cls(item)


class DependencyProvider:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.cache = {}
        self.resolve_map = {
            "session": self.provide_session,
        }
        self.teardown_map = {
            "session": self.teardown_session,
        }

    @staticmethod
    def add_global(name: str, obj: ...) -> None:
        GLOBALS[name] = (obj, set())

    @staticmethod
    def resolve_dependency_list(func: Callable) -> list[tuple[str, str]]:
        signature = inspect.signature(func)
        return [
            (arg_name, arg_value.default.option)
            for arg_name, arg_value in signature.parameters.items()
            if isinstance(arg_value.default, Provide)
        ]

    def provide_dependency(self, name: str, class_name: str, dependencies: list[str]) -> tuple[object, set[str]]:
        if name in GLOBALS:
            return GLOBALS[name]

        if name in self.cache:
            return self.cache[name]

        module_name, relative_class_name = class_name.rsplit(".", 1)
        module = import_module(module_name)
        class_ = getattr(module, relative_class_name)
        deps = {}
        dep_set = set(dependencies)

        for dependency in dependencies:
            dep_info = DEPENDENCIES[dependency]
            dep_class_name = dep_info["class_"]
            dep_dependencies = dep_info.get("depends", [])
            dep_instance, dep_set_ = self.provide_dependency(dependency, dep_class_name, dep_dependencies)
            dep_set |= dep_set_
            deps[dependency] = dep_instance
            self.cache[dependency] = dep_instance, dep_set_

        instance = class_(**deps)

        if name in self.resolve_map:
            instance = self.resolve_map[name](instance)

        return instance, dep_set

    def invalidate_cache(self, key: str) -> None:
        if key not in self.cache:
            return

        del self.cache[key]

        for dep_key, dep in DEPENDENCIES.items():
            if key in dep.get("depends", []):
                self.invalidate_cache(dep_key)

    @staticmethod
    def provide_session(session_manager: SessionManager) -> Session:
        session = session_manager.get_session()
        session.begin()
        return session

    @staticmethod
    def teardown_session(session: Session) -> None:
        session.commit()
        session.close()


def inject(func: Callable) -> Callable:
    provider = DependencyProvider()
    dep_list = provider.resolve_dependency_list(func)

    @wraps(func)
    def decorated(*args, **kwargs):
        deps = {}
        for arg_name, dep_name in dep_list:
            dep_info = DEPENDENCIES[dep_name]
            dep_class_name = dep_info["class_"]
            dep_dependencies = dep_info.get("depends", [])
            deps[arg_name] = provider.provide_dependency(dep_name, dep_class_name, dep_dependencies)

        dep_kwargs = {dep_name: dep for dep_name, (dep, _) in deps.items()}
        result = func(*args, **kwargs, **dep_kwargs)

        def _teardown_and_invalidate(dep_name_: str, dep_: object) -> None:
            if dep_name_ in provider.teardown_map:
                provider.teardown_map[dep_name_](dep_)
                provider.invalidate_cache(dep_name_)

        for dep_name, (dep, dep_set) in deps.items():
            _teardown_and_invalidate(dep_name, dep)
            for nested_dep in dep_set:
                provider.invalidate_cache(nested_dep)

        return result

    return decorated
