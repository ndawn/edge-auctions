from auctions.db.models.external import ExternalToken
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.external import ExternalTokenSerializer

blueprint = create_crud_blueprint(
    model=ExternalToken,
    serializer_name="external_token_serializer",
    create_args=ExternalTokenSerializer(),
    update_args=ExternalTokenSerializer(partial=True),
)
