import re
from datetime import datetime
from datetime import timezone
from string import ascii_uppercase
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from bs4 import Tag  # noqa
from dateutil.relativedelta import relativedelta

from auctions.db.models.enum import SupplyItemParseStatus
from auctions.db.models.items import Item
from auctions.db.models.price_categories import PriceCategory
from auctions.db.repositories.item_types import ItemTypesRepository
from auctions.db.repositories.price_categories import PriceCategoriesRepository
from auctions.dependencies import injectable
from auctions.exceptions import ObjectDoesNotExist
from auctions.exceptions import TooManyImages
from auctions.services.images_service import ImagesService


@injectable
class ParseService:
    def __init__(
        self,
        images_service: ImagesService,
        item_types_repository: ItemTypesRepository,
        price_categories_repository: PriceCategoriesRepository,
    ) -> None:
        self.images_service = images_service
        self.item_types_repository = item_types_repository
        self.price_categories_repository = price_categories_repository

        self.stashmycomics_url = "https://stashmycomics.com/"
        self.stashmycomics_series_search_url = "searchpreresults.asp"
        self.stashmycomics_series_search_page = f"{self.stashmycomics_url}/{self.stashmycomics_series_search_url}"
        self.stashmycomics_issue_search_url = "searchresults.asp"
        self.stashmycomics_issue_search_page = f"{self.stashmycomics_url}/{self.stashmycomics_issue_search_url}"
        self.stashmycomics_item_url = "searchviewcomic.asp"
        self.stashmycomics_item_page = f"{self.stashmycomics_url}/{self.stashmycomics_item_url}"
        self.alternative_url = "https://www.comics.org"
        self.datetime_patterns = (
            "%B %Y",
            "[%B] %Y",
            "(%B %Y)",
            "([%B] %Y)",
        )

    def process_item(self, item: Item) -> Item:
        if len(item.images) > 1:
            raise TooManyImages("Item must have only one image to perform parsing")

        if not item.upca and not item.upc5:
            item.upca, item.upc5 = self.images_service.scan_barcode(item.images[0])

        return self.parse_item_data(item)

    def parse_item_data(self, item: Item) -> Item:
        if None in (item.upca, item.upc5):
            item.parse_status = SupplyItemParseStatus.FAILED
            return item

        try:
            parsed_data = self._fetch_barcode_data(item.upca + item.upc5)
        except Exception:
            item.parse_status = SupplyItemParseStatus.FAILED
            return item

        if parsed_data.get("series_name") and parsed_data.get("issue_number"):
            item.name = f'{parsed_data["series_name"]} #{parsed_data["issue_number"]}'.upper()

        item.parse_data["description"] = parsed_data.get("description", "")
        item.parse_data["publisher"] = parsed_data.get("publisher")
        item.parse_data["release_date"] = parsed_data.get("release_date")
        item.parse_data["cover_price"] = parsed_data.get("cover_price")
        item.parse_data["condition_prices"] = parsed_data.get("condition_prices", {})
        item.parse_data["related_links"] = parsed_data.get("related_links", [])
        item.price_category = item.session.item_type.price_category

        if item.price_category is None:
            item.price_category = self._parse_item_price(item)

        if item.name and item.price_category is not None:
            item.parse_status = SupplyItemParseStatus.SUCCESS
        else:
            item.parse_status = SupplyItemParseStatus.FAILED

        return item

    def _parse_item_data_alternative(self, upc: str) -> dict:
        parsed_data: dict[str, ...] = {"status": SupplyItemParseStatus.SUCCESS}

        response = requests.get(f"{self.stashmycomics_series_search_page}?upc={upc}")
        page = BeautifulSoup(response.text)

        link_element = page.select_one("#TitleResults a")

        if link_element is None:
            parsed_data |= self._fetch_barcode_data(upc)
            return parsed_data

        publisher = page.select_one("#TitleResults small")

        if publisher is not None:
            parsed_data["publisher"] = publisher.text.strip()

        link = link_element.get("href")

        series_id = re.search(rf"{self.stashmycomics_issue_search_url}\?.*seriesid=(\d+).*", link)
        if series_id is not None:
            parsed_data["series_id"] = series_id.groups()[0]

        parsed_data["series_name"] = link_element.text.strip()

        response = requests.get(f"{self.stashmycomics_url}{link}")
        page = BeautifulSoup(response.text)

        table_columns = page.select("#IssueResults tbody td")

        link = table_columns[1].select_one("a")

        if link is None:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        link = link.get("href")

        parsed_data.setdefault("related_links", []).append(f"{self.stashmycomics_url}{link}")

        issue_number = table_columns[1].text.strip()

        parsed_data["issue_number"] = parsed_data["issue_variant"] = ""

        for ch in issue_number:
            parsed_data["issue_number" if ch.isdigit() else "issue_variant"] += ch

        if not parsed_data["issue_number"]:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        parsed_data["release_date"] = datetime.strptime(table_columns[2].text.strip(), "%B, %Y")
        parsed_data["issue_info"] = table_columns[3].text.strip()

        issue_id = re.search(rf"{self.stashmycomics_item_url}\?kcid=(\d+)", link)

        if issue_id is None:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        parsed_data["issue_id"] = issue_id.groups()[0]

        response = requests.get(f"{self.stashmycomics_url}{link}")
        page = BeautifulSoup(response.text)

        try:
            cover_price_element = page.select("section.row")[1]
            cover_price = re.search(r"and went on sale .+ for \$(\d+\.\d+) USD", cover_price_element.text)

            if cover_price is not None:
                parsed_data["cover_price"] = float(cover_price.groups()[0])
            else:
                parsed_data["cover_price"] = None
        except (IndexError, AttributeError):
            parsed_data["cover_price"] = None

        parsed_data_ = self._parse_item_condition_prices(
            parsed_data,
            parsed_data["series_name"],
            parsed_data["issue_number"],
            parsed_data.get("release_date").year if "release_date" in parsed_data else None,
        )

        parsed_data_.setdefault("related_links", []).extend(parsed_data.get("related_links", []))
        parsed_data |= parsed_data_

        return parsed_data

    def _fetch_barcode_data(self, upc: str) -> dict[str, ...]:
        parsed_data: dict[str, ...] = {"status": SupplyItemParseStatus.SUCCESS}

        response = requests.get(f"https://www.comics.org/barcode/{upc}/")
        page = BeautifulSoup(response.text)

        table_rows: list[Tag] = page.select("table.listing tr")

        if len(table_rows) < 2:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        issue_row = table_rows[1]

        issue_col: Tag = issue_row.select("td")[2]
        issue_links: list[Tag] = issue_col.select("a")

        if len(issue_links) < 2:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        issue_link = issue_links[-1].get("href")

        response = requests.get(f"{self.alternative_url}{issue_link}")
        page = BeautifulSoup(response.text)

        price_element = page.select_one("#issue_price")

        if price_element is None:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        parsed_data.setdefault("related_links", []).append(f"{self.alternative_url}{issue_link}")

        cover_price = re.search(r"(\d+\.\d+) USD", price_element.text)

        if cover_price is None:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        parsed_data["cover_price"] = float(cover_price.groups()[0])

        series_and_issue = page.select_one("#series_and_issue")

        if series_and_issue is None:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        series_name = series_and_issue.select_one("#series_name")

        if series_name is None:
            parsed_data["status"] = SupplyItemParseStatus.FAILED
            return parsed_data

        parsed_data["series_name"] = series_name.text.strip()

        issue_number = series_and_issue.select_one("span.issue_number")

        if issue_number is None:
            parsed_data["issue_number"] = ""
            parsed_data["issue_variant"] = ""
        else:
            parsed_data["issue_number"] = issue_number.text.strip().replace("#", "")

            series_and_issue_last_child = list(series_and_issue.children)[-1].strip()

            issue_level_content = page.select_one(".issue_level_content")

            if issue_level_content is not None and "This issue has variants" in issue_level_content.text:
                parsed_data["issue_variant"] = "A"
            else:
                parsed_data["issue_variant"] = self._parse_item_variant_from_cover_gallery(
                    page,
                    parsed_data["issue_number"],
                    series_and_issue_last_child.strip(),
                )

                if parsed_data["issue_variant"] is None:
                    parsed_data["status"] = SupplyItemParseStatus.FAILED
                    return parsed_data

        publisher = page.select_one("#issue_indicia_publisher")

        if publisher is not None:
            parsed_data["publisher"] = publisher.text.strip()

        release_date = page.select_one("h1.item_id .right")

        if release_date is not None:
            for pattern in self.datetime_patterns:
                try:
                    parsed_data["release_date"] = datetime.strptime(
                        release_date.text.strip(),
                        pattern,
                    )
                    break
                except ValueError:
                    continue
            else:
                parsed_data["release_date"] = None

        parsed_data_ = self._parse_item_condition_prices(
            parsed_data,
            parsed_data["series_name"],
            parsed_data["issue_number"],
            parsed_data.get("release_date").year if "release_date" in parsed_data else None,
        )

        parsed_data_.setdefault("related_links", []).extend(parsed_data.get("related_links", []))
        parsed_data |= parsed_data_

        return parsed_data

    def _parse_item_variant_from_cover_gallery(
        self,
        page: BeautifulSoup,
        issue_number: str,
        issue_alias: str,
    ) -> str | None:
        issue_cover_gallery = page.select_one(".issue_cover_links .right a")

        if issue_cover_gallery is None:
            return ""

        response = requests.get(f'{self.alternative_url}{issue_cover_gallery.get("href")}')
        page_ = BeautifulSoup(response.text)

        cover_list = list(
            map(
                lambda element: element.text.strip(),
                filter(
                    lambda element: element.find("a", text=re.compile(issue_number)),
                    page_.select(".cover_number"),
                ),
            )
        )

        if len(cover_list) == 1:
            return ""

        try:
            cover_index = cover_list.index(f'{issue_number}{(" " + issue_alias) if issue_alias else ""}')
        except ValueError:
            return None

        return ascii_uppercase[cover_index]

    @staticmethod
    def _parse_item_condition_prices(
        parsed_data: dict,
        series_name: str,
        issue_number: str,
        release_year: int | None,
    ) -> dict[str, ...]:
        if release_year is None:
            return {}

        parsed_data_: dict[str, ...] = {"condition_prices": {}}

        query_params = {
            "q": f"{series_name.lower()} #{issue_number}",
            "minyr": release_year - 1,
            "maxyr": release_year + 1,
        }

        url = f"https://www.mycomicshop.com/search?{urlencode(query_params)}"

        response = requests.get(url)
        page = BeautifulSoup(response.text)

        issues = page.select("#resultstab .issue")
        issue_element = next(
            filter(
                lambda el: el.find(
                    "strong",
                    string=f'#{parsed_data["issue_number"]}{parsed_data["issue_variant"]}',
                ),
                issues,
            ),
            None,
        )

        if issue_element is None:
            parsed_data_["status"] = SupplyItemParseStatus.FAILED
            return parsed_data_

        parsed_data_.setdefault("related_links", []).append(url)

        cover_price_element = issue_element.select_one(".tabcontents > p")

        if cover_price_element is not None:
            parsed_data_["description"] = cover_price_element.text.strip()

            if parsed_data.get("cover_price") is None:
                cover_price = re.search(r"Cover price \$(\d+\.\d+)\.", cover_price_element.text.strip())

                if cover_price is None:
                    parsed_data_["status"] = SupplyItemParseStatus.FAILED
                    return parsed_data_

                parsed_data_["cover_price"] = float(cover_price.groups()[0])

        prices = issue_element.select("td:not(.highlighted)")

        for price_element in reversed(prices):
            price_meta = price_element.select_one('meta[itemprop="price"]')

            if price_meta is None:
                continue

            issue_condition_price = float(price_meta.get("content").strip())

            issue_condition_name = price_element.select_one(".addcart").text
            issue_condition_name = issue_condition_name.replace("Add to cart", "").strip()
            parsed_data_["condition_prices"][issue_condition_name] = issue_condition_price

        return parsed_data_

    def _parse_item_price(self, item: Item) -> PriceCategory | None:
        if item.parse_data.get("cover_price") is None or item.parse_data.get("release_date") is None:
            return None

        if item.parse_data["release_date"] + relativedelta(months=6) >= datetime.now(timezone.utc):
            acceptable_conditions = ["Near Mint", "Very Fine"]
            min_price_delta = 2
            to_pass = True
            price_map = {
                3.99: 400,
                4.99: 500,
                5.99: 600,
                6.99: 600,
                7.99: 800,
                8.99: 800,
                9.99: 800,
            }
        else:
            acceptable_conditions = ["Near Mint", "Very Fine", "Fine", "Very Good"]
            min_price_delta = 3
            to_pass = False
            price_map = {
                4: 400,
                3.5: 350,
                3: 300,
                2.5: 250,
                2: 200,
            }

        for condition in acceptable_conditions:
            if condition not in item.parse_data["condition_prices"]:
                continue

            if (
                item.parse_data["condition_prices"][condition] + min_price_delta >= item.parse_data["cover_price"]
            ) != to_pass:
                return None

            base_price = item.parse_data["cover_price"] if to_pass else item.parse_data["condition_prices"][condition]

            try:
                return self.price_categories_repository.get_one(
                    (PriceCategory.usd == base_price)
                    & (PriceCategory.rub == price_map.get(base_price)),
                )
            except ObjectDoesNotExist:
                pass

        return None
