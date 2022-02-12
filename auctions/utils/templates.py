import re

from auctions.comics.models import Item, ItemDescriptionTemplate


TEMPLATE_TAG_MAP = [
    ('name', lambda item: item.name),
    ('type', lambda item: item.type.name),
    ('buy_now_price', lambda item: (item.price_category or item.type.price_category).buy_now_price),
    ('buy_now_expires', lambda item: (item.price_category or item.type.price_category).buy_now_expires),
    ('bid_start_price', lambda item: (item.price_category or item.type.price_category).bid_start_price),
    ('bid_min_step', lambda item: (item.price_category or item.type.price_category).bid_min_step),
    ('bid_multiple_of', lambda item: (item.price_category or item.type.price_category).bid_multiple_of),
]


WRAP_TAG_NAME = 'include'


def build_template(text: str, item: Item) -> str:
    output = ''

    for tag, get_tag in TEMPLATE_TAG_MAP:
        if re.search(r'{ ?%s ?}' % tag, text) is not None:
            output = re.sub(r'{ ?%s ?}' % tag, get_tag(item), text)

    return output


def build_description(item: Item) -> str:
    description = item.description
    if item.wrap_to is not None:
        description = re.sub(r'{ ?%s ?}' % WRAP_TAG_NAME, description, item.wrap_to.text)

    description = build_template(description, item)
    return description
