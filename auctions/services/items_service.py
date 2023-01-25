from collections import defaultdict

from auctions.config import Config
from auctions.db.models.enum import SupplyItemParseStatus
from auctions.db.models.items import Item
from auctions.db.repositories.items import ItemsRepository
from auctions.db.repositories.item_types import ItemTypesRepository
from auctions.dependencies import injectable


@injectable
class ItemsService:
    def __init__(
        self,
        items_repository: ItemsRepository,
        item_types_repository: ItemTypesRepository,
        config: Config,
    ) -> None:
        self.items_repository = items_repository
        self.item_types_repository = item_types_repository
        self.config = config

    def list_items(self, filters: dict[str, ...]) -> list[Item]:
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

    def get_counters(self) -> list[dict[str, ...]]:
        item_types = self.item_types_repository.get_many(with_pagination=False)

        counters = []
        price_categories = {}

        for item_type in item_types:
            price_categories_counters = defaultdict(int)

            counter = {
                "item_type": item_type,
                "prices": [],
            }

            for item in item_type.items:
                if item.auction is not None:
                    continue

                if item.price_category.id not in price_categories:
                    price_categories[item.price_category.id] = item.price_category

                price_categories_counters[item.price_category.id] += 1

            for price_category_id in price_categories_counters:
                counter["prices"].append({
                    "price_category": price_categories[price_category_id],
                    "count": price_categories_counters[price_category_id],
                })

            counters.append(counter)

        return counters

    def get_random_set(self, amounts: dict[int, dict[int, int]]) -> list[Item]:
        return self.items_repository.get_random_set(amounts)

    def get_random_item_for_auction(
        self,
        item_type_id: int,
        price_category_id: int,
        exclude_ids: list[int],
    ) -> Item | None:
        return self.items_repository.get_random_one(item_type_id, price_category_id, exclude_ids)

    def update_item(self, id_: int, data: dict[str, ...]) -> Item:
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
