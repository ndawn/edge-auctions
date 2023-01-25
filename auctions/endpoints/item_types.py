from webargs import fields

from auctions.db.models.item_types import ItemType
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.item_types import ItemTypeSerializer

blueprint = create_crud_blueprint(
    model=ItemType,
    serializer_class=ItemTypeSerializer,
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=10),
    },
    create_args=ItemTypeSerializer(),
    update_args=ItemTypeSerializer(partial=True),
)
