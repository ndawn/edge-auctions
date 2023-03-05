from webargs import fields

from auctions.db.models.users import User
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.users import UserSerializer

blueprint = create_crud_blueprint(
    model=User,
    serializer_class=UserSerializer,
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=20),
    },
    operations=(
        "list",
        "update",
        "delete",
    ),
    create_args=UserSerializer(),
    update_args=UserSerializer(partial=True),
    non_int_id=True,
)
