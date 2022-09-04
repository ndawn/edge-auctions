from typing import Any

from flask import current_app

from auctions.config import Config
from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.enum import SupplyItemParseStatus
from auctions.db.models.items import Item
from auctions.db.repositories.items import ItemsRepository


class ItemsService:
    def __init__(self, items_repository: ItemsRepository) -> None:
        self.items_repository = items_repository
        self.config: Config = current_app.config["config"]

    def list_items(self, filters: dict[str, Any]) -> list[Item]:
        filter_predicate = (Item.auction == None) & (Item.session == None)

        item_type_id = filters.get("item_type_id")
        price_category_id = filters.get("price_category_id")
        page = filters.get("page")
        page_size = filters.get("page_size")

        if item_type_id:
            filter_predicate &= (Item.type_id == item_type_id)

        if price_category_id:
            filter_predicate &= (Item.price_category_id == price_category_id)

        return self.items_repository.get_many(filter_predicate, page=page, page_size=page_size)

    def update_item(self, id_: int, data: dict[str, Any]) -> Item:
        item = self.items_repository.get_one_by_id(id_)

        item_mandatory_fields = {
            "name": item.name or data.get("name"),
            "price_category_id": item.price_category_id or data.get("price_category_id"),
            "upca": item.upca or data.get("upca"),
            "upc5": item.upc5 or data.get("upc5"),
        }

        if (
                item.parse_status != SupplyItemParseStatus.SUCCESS
                and item_mandatory_fields["name"] and item_mandatory_fields["price_category_id"]
        ):
            data["parse_status"] = SupplyItemParseStatus.SUCCESS
        elif (
                item.parse_status != SupplyItemParseStatus.SUCCESS
                and item_mandatory_fields["upca"] and item_mandatory_fields["upc5"]
                and (not item.upca or not item.upc5)
        ):
            data["parse_status"] = SupplyItemParseStatus.PENDING

        self.items_repository.update(item, **data)
        return item

    def delete_items(self, ids: list[int]) -> None:
        if not ids:
            return

        items = self.items_repository.get_many(ids=ids)
        self.items_repository.delete(items)
