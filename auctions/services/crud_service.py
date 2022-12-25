from copy import deepcopy
from typing import Any
from typing import Iterable
from typing import Type
from typing import Union

from sqlalchemy import true
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import BooleanClauseList

from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auction_targets import AuctionTargetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.base import Model
from auctions.db.repositories.base import Repository
from auctions.db.repositories.bidders import BiddersRepository
from auctions.db.repositories.bids import BidsRepository
from auctions.db.repositories.external import ExternalEntitiesRepository
from auctions.db.repositories.external import ExternalTokensRepository
from auctions.db.repositories.images import ImagesRepository
from auctions.db.repositories.item_types import ItemTypesRepository
from auctions.db.repositories.items import ItemsRepository
from auctions.db.repositories.price_categories import PriceCategoriesRepository
from auctions.db.repositories.sessions import SupplySessionsRepository
from auctions.db.repositories.templates import TemplatesRepository
from auctions.db.repositories.users import AuthTokensRepository
from auctions.db.repositories.users import ExternalUsersRepository
from auctions.db.repositories.users import UsersRepository
from auctions.exceptions import BadRequestError
from auctions.exceptions import HTTPError
from auctions.exceptions import ObjectDoesNotExist


class CRUDServiceProvider:
    __instance = None

    def __new__(cls, *args, **kwargs) -> "CRUDServiceProvider":  # pylint: disable=unused-argument
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    def __init__(
        self,
        auction_sets_repository: AuctionSetsRepository,
        auction_targets_repository: AuctionTargetsRepository,
        auctions_repository: AuctionsRepository,
        bidders_repository: BiddersRepository,
        bids_repository: BidsRepository,
        external_entities_repository: ExternalEntitiesRepository,
        external_tokens_repository: ExternalTokensRepository,
        external_users_repository: ExternalUsersRepository,
        images_repository: ImagesRepository,
        item_types_repository: ItemTypesRepository,
        items_repository: ItemsRepository,
        price_categories_repository: PriceCategoriesRepository,
        supply_sessions_repository: SupplySessionsRepository,
        templates_repository: TemplatesRepository,
        auth_tokens_repository: AuthTokensRepository,
        users_repository: UsersRepository,
    ) -> None:
        self.cache = {}
        self.repositories = [
            auction_sets_repository,
            auction_targets_repository,
            auctions_repository,
            bidders_repository,
            bids_repository,
            external_entities_repository,
            external_tokens_repository,
            external_users_repository,
            images_repository,
            item_types_repository,
            items_repository,
            price_categories_repository,
            supply_sessions_repository,
            templates_repository,
            auth_tokens_repository,
            users_repository,
        ]

    def __call__(self, model: Type[Model]) -> "CRUDService":
        if model not in self.cache:
            self.cache[model] = CRUDService(self.get_repository(model), self)

        return self.cache[model]

    def get_repository(self, model: Type[Model]) -> Repository:
        for repository in self.repositories:
            if repository.model is model:
                return repository

        raise ObjectDoesNotExist(f"No repository found for model {model}")


class CRUDService:
    model: Type[Model]
    repository: Repository

    def __init__(self, repository: Repository, provider: CRUDServiceProvider) -> None:
        self.provider = provider
        self.repository = repository
        self.model = self.repository.model

    def list(self, filters: BooleanClauseList = true(), page: int = 0, page_size: int = None) -> list[Model]:
        if page_size is None:
            page_size = self.repository.default_page_size

        return self.repository.get_many(filters=filters, page=page, page_size=page_size)

    def get(self, id_: int) -> Model:
        return self.repository.get_one_by_id(id_)

    def create(self, **kwargs) -> Model:
        kwargs = self._update_with_related_objects(kwargs)
        return self.repository.create(**kwargs)

    def update(self, id_: int, **kwargs) -> Model:
        instance = self.repository.get_one_by_id(id_)
        kwargs = self._update_with_related_objects(kwargs)
        self.repository.update(instance, **kwargs)
        return instance

    def delete(self, id_: Union[int, Iterable[int]]) -> None:
        if isinstance(id_, int):
            ids = [id_]
        else:
            ids = id_

        instances = self.repository.get_many(ids=ids)
        id_set = {instance.id for instance in instances}
        difference = set(ids) - id_set

        if difference:
            raise ObjectDoesNotExist(f'{self.model.__name__} with ids {", ".join(map(str, difference))} do not exist')

        self.repository.delete(instances)

    def _get_foreign_key_fields(self) -> dict[str, InstrumentedAttribute]:
        return {
            key: field
            for key, field in self.model.__dict__.items()
            if isinstance(field, InstrumentedAttribute)
            and hasattr(field.property, "columns")
            and field.property.columns[0].foreign_keys
        }

    def _find_related_model_by_foreign_key_name(self, key: str) -> tuple[Type[Model], str]:
        relationship_key = None
        model = None

        for relationship in self.model.__mapper__.relationships.values():
            try:
                foreign_key = list(relationship.local_columns)[0]
            except (KeyError, IndexError):
                continue

            if foreign_key.key != key:
                continue

            relationship_key = relationship.key
            model = relationship.mapper.class_

        if relationship_key is None or model is None:
            raise HTTPError(f'No relationship found for key "{key}"')

        return model, relationship_key

    def _update_with_related_objects(self, data: dict[str, Any]) -> dict[str, Model]:
        result = deepcopy(data)

        foreign_key_fields = self._get_foreign_key_fields()

        for key, value in data.items():
            if key not in foreign_key_fields:
                continue

            if value is None:
                if not foreign_key_fields[key].property.columns[0].nullable:  # type: ignore
                    raise BadRequestError(f'Field "{key}" cannot be empty')
                result[key] = None
                continue

            model, relationship_key = self._find_related_model_by_foreign_key_name(key)
            model_instance = self.provider(model).get(value)
            result[relationship_key] = model_instance
            del result[key]

        return result
