from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from string import ascii_uppercase
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup, NavigableString, Tag  # type: ignore
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from auctions.comics.models import PriceCategory
from auctions.supply.models import SupplyItem, SupplyItemParseStatus


STASHMYCOMICS_URL = 'https://stashmycomics.com/'
STASHMYCOMICS_SERIES_SEARCH_URL = 'searchpreresults.asp'
STASHMYCOMICS_SERIES_SEARCH_PAGE = f'{STASHMYCOMICS_URL}/{STASHMYCOMICS_SERIES_SEARCH_URL}'
STASHMYCOMICS_ISSUE_SEARCH_URL = 'searchresults.asp'
STASHMYCOMICS_ISSUE_SEARCH_PAGE = f'{STASHMYCOMICS_URL}/{STASHMYCOMICS_ISSUE_SEARCH_URL}'
STASHMYCOMICS_ITEM_URL = 'searchviewcomic.asp'
STASHMYCOMICS_ITEM_PAGE = f'{STASHMYCOMICS_URL}/{STASHMYCOMICS_ITEM_URL}'
ALTERNATIVE_URL = 'https://www.comics.org'

DATETIME_PATTERNS = (
    '%B %Y',
    '[%B] %Y',
    '(%B %Y)',
    '([%B] %Y)',
)


async def parse_item_data(item: SupplyItem) -> SupplyItem:
    if None in (item.upca, item.upc5):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Cannot parse item with upca or upc5 not set',
        )

    async with aiohttp.ClientSession() as session:
        try:
            parsed_data = await _parse_item_data(item.upca + item.upc5, session)
        except:  # noqa
            item.parse_status = SupplyItemParseStatus.FAILED
            await item.save()
            return item

    await item.fetch_related('session__item_type__price_category')

    if parsed_data.get('series_name') and parsed_data.get('issue_number'):
        item.name = f'{parsed_data["series_name"]} #{parsed_data["issue_number"]}'

    item.source_description = parsed_data.get('description', '')
    item.publisher = parsed_data.get('publisher')
    item.release_date = parsed_data.get('issue_publication_date')
    item.cover_price = parsed_data.get('cover_price')
    item.condition_prices = parsed_data.get('condition_prices', {})
    item.related_links = parsed_data.get('related_links', [])
    item.price_category = item.session.item_type.price_category

    if item.price_category is None:
        item.price_category = await _parse_item_price(item)

    item.parse_status = parsed_data.get('status', SupplyItemParseStatus.FAILED)
    if item.name is not None and item.price_category is not None:
        item.parse_status = SupplyItemParseStatus.SUCCESS

    await item.save()
    return item


async def _parse_item_data_alternative(upc: str, session: aiohttp.ClientSession) -> dict:
    parsed_data: dict[str, Any] = {'status': SupplyItemParseStatus.SUCCESS}

    async with session.get(f'{STASHMYCOMICS_SERIES_SEARCH_PAGE}?upc={upc}') as response:
        page = BeautifulSoup(await response.text())

    link_element = page.select_one('#TitleResults a')

    if link_element is None:
        parsed_data |= await _parse_item_data(upc, session)
        return parsed_data

    publisher = page.select_one('#TitleResults small')

    if publisher is not None:
        parsed_data['publisher'] = publisher.text.strip()

    link = link_element.get('href')

    series_id = re.search(f'{STASHMYCOMICS_ISSUE_SEARCH_URL}\?.*seriesid=(\d+).*', link)
    if series_id is not None:
        parsed_data['series_id'] = series_id.groups()[0]

    parsed_data['series_name'] = link_element.text.strip()

    async with session.get(f'{STASHMYCOMICS_URL}{link}') as response:
        page = BeautifulSoup(await response.text())

    table_columns = page.select('#IssueResults tbody td')

    link = table_columns[1].select_one('a')

    if link is None:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    link = link.get('href')

    parsed_data.setdefault('related_links', []).append(f'{STASHMYCOMICS_URL}{link}')

    issue_number = table_columns[1].text.strip()

    parsed_data['issue_number'] = parsed_data['issue_variant'] = ''

    for ch in issue_number:
        parsed_data['issue_number' if ch.isdigit() else 'issue_variant'] += ch

    if not parsed_data['issue_number']:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    parsed_data['issue_publication_date'] = datetime.strptime(table_columns[2].text.strip(), '%B, %Y')
    parsed_data['issue_info'] = table_columns[3].text.strip()

    issue_id = re.search(f'{STASHMYCOMICS_ITEM_URL}\?kcid=(\d+)', link)

    if issue_id is None:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    parsed_data['issue_id'] = issue_id.groups()[0]

    async with session.get(f'{STASHMYCOMICS_URL}{link}') as response:
        page = BeautifulSoup(await response.text())

    try:
        cover_price_element = page.select('section.row')[1]
        cover_price = re.search(r'and went on sale .+ for \$(\d+\.\d+) USD', cover_price_element.text)

        if cover_price is not None:
            parsed_data['cover_price'] = float(cover_price.groups()[0])
        else:
            parsed_data['cover_price'] = None
    except (IndexError, AttributeError):
        parsed_data['cover_price'] = None

    parsed_data_ = await _parse_item_condition_prices(
        parsed_data,
        parsed_data['series_name'],
        parsed_data['issue_number'],
        parsed_data.get('issue_publication_date').year if 'issue_publication_date' in parsed_data else None,
    )

    parsed_data_.setdefault('related_links', []).extend(parsed_data.get('related_links', []))
    parsed_data |= parsed_data_

    return parsed_data


async def _parse_item_data(upc: str, session: aiohttp.ClientSession) -> dict:
    parsed_data: dict[str, Any] = {'status': SupplyItemParseStatus.SUCCESS}

    async with session.get(f'https://www.comics.org/barcode/{upc}/') as response:
        page = BeautifulSoup(await response.text())

    table_rows: list[Tag] = page.select('table.listing tr')

    if len(table_rows) < 2:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    issue_row = table_rows[1]

    issue_col: Tag = issue_row.select('td')[2]
    issue_links: list[Tag] = issue_col.select('a')

    if len(issue_links) < 2:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    issue_link = issue_links[-1].get('href')

    async with session.get(f'{ALTERNATIVE_URL}{issue_link}') as response:
        page = BeautifulSoup(await response.text())

    price_element = page.select_one('#issue_price')

    if price_element is None:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    parsed_data.setdefault('related_links', []).append(f'{ALTERNATIVE_URL}{issue_link}')

    cover_price = re.search(r'(\d+\.\d+) USD', price_element.text)

    if cover_price is None:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    parsed_data['cover_price'] = float(cover_price.groups()[0])

    series_and_issue = page.select_one('#series_and_issue')

    if series_and_issue is None:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    series_name = series_and_issue.select_one('#series_name')

    if series_name is None:
        parsed_data['status'] = SupplyItemParseStatus.FAILED
        return parsed_data

    parsed_data['series_name'] = series_name.text.strip()

    issue_number = series_and_issue.select_one('span.issue_number')

    if issue_number is None:
        parsed_data['issue_number'] = ''
        parsed_data['issue_variant'] = ''
    else:
        parsed_data['issue_number'] = issue_number.text.strip().replace('#', '')

        series_and_issue_last_child = list(series_and_issue.children)[-1].strip()

        issue_level_content = page.select_one('.issue_level_content')

        if issue_level_content is not None and 'This issue has variants' in issue_level_content.text:
            parsed_data['issue_variant'] = 'A'
        else:
            parsed_data['issue_variant'] = await _parse_item_variant_from_cover_gallery(
                page,
                parsed_data['issue_number'],
                series_and_issue_last_child.strip(),
                session,
            )

            if parsed_data['issue_variant'] is None:
                parsed_data['status'] = SupplyItemParseStatus.FAILED
                return parsed_data

    publisher = page.select_one('#issue_indicia_publisher')

    if publisher is not None:
        parsed_data['publisher'] = publisher.text.strip()

    issue_publication_date = page.select_one('h1.item_id .right')

    if issue_publication_date is not None:
        for pattern in DATETIME_PATTERNS:
            try:
                parsed_data['issue_publication_date'] = datetime.strptime(issue_publication_date.text.strip(), pattern)
                break
            except ValueError:
                continue
        else:
            parsed_data['issue_publication_date'] = None

    parsed_data_ = await _parse_item_condition_prices(
        parsed_data,
        parsed_data['series_name'],
        parsed_data['issue_number'],
        parsed_data.get('issue_publication_date').year if 'issue_publication_date' in parsed_data else None,
    )

    parsed_data_.setdefault('related_links', []).extend(parsed_data.get('related_links', []))
    parsed_data |= parsed_data_

    return parsed_data


async def _parse_item_variant_from_cover_gallery(
    page: BeautifulSoup,
    issue_number: str,
    issue_alias: str,
    session: aiohttp.ClientSession,
) -> Optional[str]:
    issue_cover_gallery = page.select_one('.issue_cover_links .right a')

    if issue_cover_gallery is None:
        return ''

    async with session.get(f'{ALTERNATIVE_URL}{issue_cover_gallery.get("href")}') as response:
        page_ = BeautifulSoup(await response.text())

    cover_list = list(
        map(
            lambda element: element.text.strip(),
            filter(
                lambda element: element.find('a', text=re.compile(issue_number)),
                page_.select('.cover_number'),
            ),
        )
    )

    if len(cover_list) == 1:
        return ''

    try:
        cover_index = cover_list.index(f'{issue_number}{(" " + issue_alias) if issue_alias else ""}')
    except ValueError:
        return None

    return ascii_uppercase[cover_index]


async def _parse_item_condition_prices(
    parsed_data: dict,
    series_name: str,
    issue_number: str,
    release_year: Optional[int],
) -> dict[str, float]:
    if release_year is None:
        return {}

    parsed_data_: dict[str, Any] = {'condition_prices': {}}

    query_params = {
        'q': f'{series_name.lower()} #{issue_number}',
        'minyr': release_year - 1,
        'maxyr': release_year + 1,
    }

    url = f'https://www.mycomicshop.com/search?{urlencode(query_params)}'

    async with aiohttp.ClientSession() as session_:
        async with session_.get(url) as response:
            page = BeautifulSoup(await response.text())

    issues = page.select('#resultstab .issue')
    issue_element = next(
        filter(
            lambda el: el.find(
                'strong',
                string=f'#{parsed_data["issue_number"]}{parsed_data["issue_variant"]}'
            ),
            issues,
        ),
        None,
    )

    if issue_element is None:
        parsed_data_['status'] = SupplyItemParseStatus.FAILED
        return parsed_data_

    parsed_data_.setdefault('related_links', []).append(url)

    cover_price_element = issue_element.select_one('.tabcontents > p')

    if cover_price_element is not None:
        parsed_data_['description'] = cover_price_element.text.strip()

        if parsed_data.get('cover_price') is None:
            cover_price = re.search(r'Cover price \$(\d+\.\d+)\.', cover_price_element.text.strip())

            if cover_price is None:
                parsed_data_['status'] = SupplyItemParseStatus.FAILED
                return parsed_data_

            parsed_data_['cover_price'] = float(cover_price.groups()[0])

    prices = issue_element.select('td:not(.highlighted)')

    for price_element in reversed(prices):
        price_meta = price_element.select_one('meta[itemprop="price"]')

        if price_meta is None:
            continue

        issue_condition_price = float(price_meta.get('content').strip())

        issue_condition_name = price_element.select_one('.addcart').text
        issue_condition_name = issue_condition_name.replace('Add to cart', '').strip()
        parsed_data_['condition_prices'][issue_condition_name] = issue_condition_price

    return parsed_data_


async def _parse_item_price(item: SupplyItem) -> Optional[PriceCategory]:
    if item.cover_price is None or item.release_date is None:
        return None

    if item.release_date + relativedelta(months=6) >= datetime.now():
        acceptable_conditions = ['Near Mint', 'Very Fine']
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
        acceptable_conditions = ['Near Mint', 'Very Fine', 'Fine', 'Very Good']
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
        if condition not in item.condition_prices:
            continue

        if (item.condition_prices[condition] + min_price_delta >= item.cover_price) != to_pass:
            return None

        base_price = item.cover_price if to_pass else item.condition_prices[condition]

        return await PriceCategory.get_or_none(
            usd=base_price,
            rub=price_map.get(base_price),
        )

    return None
