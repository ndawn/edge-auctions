from dataclasses import dataclass

from marshmallow import fields
from marshmallow import post_load
from marshmallow import EXCLUDE

from auctions.serializers.base import BaseSerializer


@dataclass
class SubscriptionInfo:
    endpoint: str
    keys: dict[str, str]


class PushSubscriptionKeysSerializer(BaseSerializer):
    p256dh = fields.Str(required=True)
    auth = fields.Str(required=True)


class PushSubscriptionInfoSerializer(BaseSerializer):
    class Meta:
        unknown = EXCLUDE

    endpoint = fields.Str(required=True)
    keys = fields.Nested("PushSubscriptionKeysSerializer", required=True)

    @post_load
    def make_dataclass(self, data: dict[str, ...], *args, **kwargs) -> SubscriptionInfo:
        return SubscriptionInfo(**data)


class AuctionBidCreatedSerializer(BaseSerializer):
    auction_id = fields.Int(required=True, data_key="auctionId")
    value = fields.Int(required=True)


class AuctionDateDueUpdatedSerializer(BaseSerializer):
    auction_id = fields.Int(required=True, data_key="auctionId")
    date_due = fields.DateTime(required=True, data_key="dateDue")
