from datetime import datetime
import re

import aiohttp
from bs4 import BeautifulSoup
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from auctions.comics.models import PriceCategory
from auctions.supply.models import SupplyItem


STASHMYCOMICS_SEARCH_PAGE = 'https://stashmycomics.com/searchresults.asp'
STASHMYCOMICS_ITEM_PAGE = 'https://stashmycomics.com/searchviewcomic.asp'


async def parse_item_data(item: SupplyItem) -> SupplyItem:
    if None in (item.upca, item.upc5):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Cannot parse item with upca or upc5 not set',
        )

    async with aiohttp.ClientSession() as session:
        parsed_data = await _parse_item_data(item.upca + item.upc5, session)

    if parsed_data.get('series_name', '') and parsed_data.get('issue_number', ''):
        item.name = f'{parsed_data["series_name"]} #{parsed_data["issue_number"]}'

    if parsed_data.get('description', ''):
        item.description = parsed_data['description']

    if parsed_data.get('price', ''):
        item.price_usd = parsed_data['price']
        price_map = await PriceCategory.get_or_none(usd=item.price_usd)

        if price_map is not None:
            item.price_rub = price_map.rub

    await item.save()
    return item


async def _parse_item_data(upc: str, session: aiohttp.ClientSession) -> dict:
    async with session.get(f'{STASHMYCOMICS_SEARCH_PAGE}?upc={upc}') as response:
        page = BeautifulSoup(await response.text())

    parsed_data = {
        'publisher': page.select_one('#TitleResults small').text.strip(),
    }

    link_element = page.select_one('#TitleResults a')
    link = link_element.get('href')

    series_id = re.search(f'{STASHMYCOMICS_SEARCH_PAGE}\?.*seriesid=(\d+).*', link)
    if series_id is not None:
        parsed_data['series_id'] = series_id.groups()[0]

    parsed_data['series_name'] = link_element.text.strip()

    async with session.get(link) as response:
        page = BeautifulSoup(await response.text())

    table_columns = page.select('#IssueResults tbody td')

    link = table_columns[1].select('a').get('href')

    parsed_data['issue_number'] = table_columns[1].text.strip()
    parsed_data['issue_publication_date'] = datetime.strptime(table_columns[2].text.strip(), '%B, %Y')
    parsed_data['issue_info'] = table_columns[3].text.strip()

    issue_id = re.search(f'{STASHMYCOMICS_ITEM_PAGE}\?kcid=(\d+)', link)

    if issue_id is not None:
        parsed_data['issue_id'] = issue_id.groups()[0]

    async with session.get(link) as response:
        page = BeautifulSoup(await response.text())

    mycomicshop_link = page.select_one('#PurchaseOptions a').get('href')

    async with session.get(mycomicshop_link) as response:
        page = BeautifulSoup(await response.text())

    issues = page.select('#resultstab .issue')
    issue_element = next(
        filter(
            lambda el: el.find('strong', string=f'#{parsed_data["issue_number"]}') is not None,
            issues,
        )
    )

    prices = issue_element.select_one('.issuestock tbody td')

    for price_element in prices:
        price_meta = price_element.select_one('meta[itemprop="price"]')

        if price_meta is not None:
            parsed_data['price'] = float(price_meta.get('content').strip())
            break

    return parsed_data
