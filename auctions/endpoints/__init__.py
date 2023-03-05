from flask import Blueprint

from auctions.endpoints.auction_sets import blueprint as auction_sets_blueprint
from auctions.endpoints.auctions import blueprint as auctions_blueprint
from auctions.endpoints.auth import blueprint as auth_blueprint
from auctions.endpoints.images import blueprint as images_blueprint
from auctions.endpoints.item_types import blueprint as item_types_blueprint
from auctions.endpoints.items import blueprint as items_blueprint
from auctions.endpoints.price_categories import blueprint as price_categories_blueprint
from auctions.endpoints.push import blueprint as push_blueprint
from auctions.endpoints.supply import blueprint as supply_blueprint
from auctions.endpoints.templates import blueprint as templates_blueprint
from auctions.endpoints.users import blueprint as users_blueprint

root_blueprint = Blueprint("root", __name__)

root_blueprint.register_blueprint(auction_sets_blueprint)
root_blueprint.register_blueprint(auctions_blueprint)
root_blueprint.register_blueprint(auth_blueprint)
root_blueprint.register_blueprint(images_blueprint)
root_blueprint.register_blueprint(item_types_blueprint)
root_blueprint.register_blueprint(items_blueprint)
root_blueprint.register_blueprint(price_categories_blueprint)
root_blueprint.register_blueprint(push_blueprint)
root_blueprint.register_blueprint(supply_blueprint)
root_blueprint.register_blueprint(templates_blueprint)
root_blueprint.register_blueprint(users_blueprint)
