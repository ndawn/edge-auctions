from webargs import fields

from auctions.db.models.auction_targets import AuctionTarget
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.auction_targets import AuctionTargetSerializer

blueprint = create_crud_blueprint(
    model=AuctionTarget,
    serializer_name="auction_target_serializer",
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    create_args=AuctionTargetSerializer(),
    update_args=AuctionTargetSerializer(partial=True),
    protected=("create", "update", "delete"),
)
