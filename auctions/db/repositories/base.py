from typing import Generic
from typing import TypeVar

from sqlalchemy import asc
from sqlalchemy import delete
from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy import true
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.elements import True_
from sqlalchemy.sql.selectable import FromClause

from auctions.config import Config
from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auctions import Auction
from auctions.db.models.bids import Bid
from auctions.db.models.enum import SortOrder
from auctions.db.models.images import Image
from auctions.db.models.item_types import ItemType
from auctions.db.models.items import Item
from auctions.db.models.price_categories import PriceCategory
from auctions.db.models.push import PushSubscription
from auctions.db.models.sessions import SupplySession
from auctions.db.models.templates import Template
from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.exceptions import ObjectDoesNotExist

Model = TypeVar(
    "Model",
    AuctionSet,
    Auction,
    Bid,
    Image,
    ItemType,
    Item,
    PriceCategory,
    PushSubscription,
    SupplySession,
    Template,
    User,
)


class Repository(Generic[Model]):
    default_page_size: int = 50
    joined_fields: tuple[InstrumentedAttribute, ...] = ()

    def __init__(self, session: Session = Provide(), config: Config = Provide()) -> None:
        self.session = session
        self.config = config

    @property
    def model(self) -> type[Model]:
        raise NotImplementedError

    @property
    def pk(self) -> InstrumentedAttribute:
        return self.model.id

    def _apply_joined_fields(self, select_statement: FromClause) -> FromClause:
        for joined_field in self.joined_fields:
            select_statement = select_statement.outerjoin(joined_field)

        return select_statement

    def create(self, instance: Model | None = None, /, **kwargs) -> Model:
        if instance is None:
            instance = self.model(**kwargs)

        self.session.add(instance)
        self.session.flush()
        return instance

    def get_many(
        self,
        filters: BooleanClauseList | True_ = true(),
        sort_key: InstrumentedAttribute | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        page_size: int = None,
        page: int = None,
        ids: list[int] = None,
        with_pagination: bool = True,
        with_joined_fields: bool = True,
    ) -> list[Model] | dict[str, int | list[Model]]:
        if sort_key is None:
            sort_key = self.pk

        if page is None:
            page = 0

        if page_size is None:
            page_size = 50

        sort_order = asc if sort_order == SortOrder.ASC else desc

        select_statement = select(self.model).where(filters).order_by(sort_order(sort_key))

        if ids is not None:
            select_statement = select_statement.where(self.pk.in_(ids))
        elif with_pagination:
            select_statement = select_statement.limit(page_size).offset(page_size * page)

        if with_joined_fields:
            select_statement = self._apply_joined_fields(select_statement)

        result = self.session.execute(select_statement).scalars().unique().all()

        if ids:
            id_set = {instance.id for instance in result}
            difference = set(ids) - id_set

            if difference:
                raise ObjectDoesNotExist(
                    f'{self.model.__name__} with ids {", ".join(map(str, difference))} do not exist'
                )

        return result

    def get_one(self, filters: BooleanClauseList = true(), with_joined_fields: bool = True) -> Model:
        select_statement = select(self.model).where(filters)

        if with_joined_fields:
            for joined_field in self.joined_fields:
                select_statement = select_statement.outerjoin(joined_field)

        result = self.session.execute(select_statement).scalar()

        if result is None:
            raise ObjectDoesNotExist(f"{self.model.__name__} with given filters does not exist")

        return result

    def get_one_by_id(self, object_id: int | str, with_joined_fields: bool = True) -> Model:
        select_statement = select(self.model).where(self.pk == object_id)

        if with_joined_fields:
            select_statement = self._apply_joined_fields(select_statement)

        result = self.session.execute(select_statement).scalar()

        if result is None:
            raise ObjectDoesNotExist(f"{self.model.__name__} with id {object_id} does not exist")

        return result

    def refresh(self, instance: Model) -> None:
        self.session.refresh(instance)

    def update(self, instance: Model, **kwargs) -> None:
        self.session.merge(instance)

        for key, value in kwargs.items():
            setattr(instance, key, value)

        self.session.flush()

    def delete(self, instances: list[Model]) -> None:
        self.session.execute(delete(self.model).where(self.pk.in_([instance.id for instance in instances])))
