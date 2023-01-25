from webargs import fields

from auctions.db.models.price_categories import PriceCategory
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.price_categories import PriceCategorySerializer

blueprint = create_crud_blueprint(
    model=PriceCategory,
    serializer_class=PriceCategorySerializer,
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=10),
    },
    create_args=PriceCategorySerializer(),
    update_args=PriceCategorySerializer(partial=True),
)
