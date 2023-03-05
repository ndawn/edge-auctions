from copy import deepcopy
from typing import Iterable

from sqlalchemy import true
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import BooleanClauseList

from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.base import Model
from auctions.db.repositories.base import Repository
from auctions.db.repositories.bids import BidsRepository
from auctions.db.repositories.images import ImagesRepository
from auctions.db.repositories.item_types import ItemTypesRepository
from auctions.db.repositories.items import ItemsRepository
from auctions.db.repositories.price_categories import PriceCategoriesRepository
from auctions.db.repositories.sessions import SupplySessionsRepository
from auctions.db.repositories.templates import TemplatesRepository
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide
from auctions.exceptions import BadRequestError
from auctions.exceptions import HTTPError
from auctions.exceptions import ObjectDoesNotExist


class CRUDServiceProvider:
    def __init__(
        self,
        auction_sets_repository: AuctionSetsRepository = Provide(),
        auctions_repository: AuctionsRepository = Provide(),
        bids_repository: BidsRepository = Provide(),
        images_repository: ImagesRepository = Provide(),
        item_types_repository: ItemTypesRepository = Provide(),
        items_repository: ItemsRepository = Provide(),
        price_categories_repository: PriceCategoriesRepository = Provide(),
        supply_sessions_repository: SupplySessionsRepository = Provide(),
        templates_repository: TemplatesRepository = Provide(),
        users_repository: UsersRepository = Provide(),
    ) -> None:
        self.cache = {}
        self.repositories = {
            auction_sets_repository.model: auction_sets_repository,
            auctions_repository.model: auctions_repository,
            bids_repository.model: bids_repository,
            images_repository.model: images_repository,
            item_types_repository.model: item_types_repository,
            items_repository.model: items_repository,
            price_categories_repository.model: price_categories_repository,
            supply_sessions_repository.model: supply_sessions_repository,
            templates_repository.model: templates_repository,
            users_repository.model: users_repository,
        }

    def __call__(self, model: type[Model]) -> "CRUDService":
        if model not in self.cache:
            self.cache[model] = CRUDService(self.get_repository(model), self)

        return self.cache[model]

    def get_repository(self, model: type[Model]) -> Repository:
        try:
            return self.repositories[model]
        except KeyError as exception:
            raise ObjectDoesNotExist(f"No repository found for model {model}") from exception


class CRUDService:
    model: type[Model]
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

    def delete(self, id_: int | str | Iterable[int] | Iterable[str]) -> None:
        if isinstance(id_, (int, str)):
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

    def _find_related_model_by_foreign_key_name(self, key: str) -> tuple[type[Model], str]:
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

    def _update_with_related_objects(self, data: dict[str, ...]) -> dict[str, Model]:
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
