from typing import Type

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.sql.selectable import FromClause

from auctions.db.models.items import Item
from auctions.db.repositories.base import Repository


class ItemsRepository(Repository[Item]):
    joined_fields = (
        Item.wrap_to,
        Item.type,
        Item.price_category,
        Item.session,
        Item.images,
    )

    @property
    def model(self) -> Type[Item]:
        return Item

    def _apply_joined_fields(self, select_statement: FromClause) -> FromClause:
        return (
            select_statement
            .outerjoin(Item.wrap_to)
            .outerjoin(Item.type)
            .outerjoin(Item.price_category)
            .outerjoin(Item.session)
            .join(Item.images)
        )

    def get_random_set(self, amounts: dict[int, dict[int, int]]) -> list[Item]:
        items = []

        for item_type_id in amounts:
            for price_category_id in amounts[item_type_id]:
                item_amount = amounts[item_type_id][price_category_id]

                if item_amount == 0:
                    continue

                filters = (
                    Item.auction.is_(None)
                    & (Item.type_id == item_type_id)
                    & (Item.price_category_id == price_category_id)
                )

                select_statement = select(Item).where(filters).order_by(func.random()).limit(item_amount)
                select_statement = self._apply_joined_fields(select_statement)
                items.extend(self.session.execute(select_statement).scalars().unique().all())

        return items
