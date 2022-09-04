from flask import Blueprint

from auctions.endpoints.accounts import blueprint as accounts_blueprint
from auctions.endpoints.auction_sets import blueprint as auction_sets_blueprint
from auctions.endpoints.auction_targets import blueprint as auction_targets_blueprint
from auctions.endpoints.auctions import blueprint as auctions_blueprint
from auctions.endpoints.external_entities import (
    blueprint as external_entities_blueprint,
)
from auctions.endpoints.external_tokens import blueprint as external_tokens_blueprint
from auctions.endpoints.images import blueprint as images_blueprint
from auctions.endpoints.item_types import blueprint as item_types_blueprint
from auctions.endpoints.items import blueprint as items_blueprint
from auctions.endpoints.price_categories import blueprint as price_categories_blueprint
from auctions.endpoints.supply import blueprint as supply_blueprint
from auctions.endpoints.templates import blueprint as templates_blueprint
from auctions.endpoints.vk import blueprint as vk_blueprint

root_blueprint = Blueprint("root", __name__)

root_blueprint.register_blueprint(accounts_blueprint)
root_blueprint.register_blueprint(auction_sets_blueprint)
root_blueprint.register_blueprint(auction_targets_blueprint)
root_blueprint.register_blueprint(auctions_blueprint)
root_blueprint.register_blueprint(external_entities_blueprint)
root_blueprint.register_blueprint(external_tokens_blueprint)
root_blueprint.register_blueprint(images_blueprint)
root_blueprint.register_blueprint(item_types_blueprint)
root_blueprint.register_blueprint(items_blueprint)
root_blueprint.register_blueprint(price_categories_blueprint)
root_blueprint.register_blueprint(supply_blueprint)
root_blueprint.register_blueprint(templates_blueprint)
root_blueprint.register_blueprint(vk_blueprint)
