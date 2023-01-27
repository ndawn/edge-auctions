from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class ShopInstallSerializer(BaseSerializer):
    shop_id = fields.Int(required=True, data_key="insales_id")
    shop_url = fields.Str(required=True, data_key="shop")
    token = fields.Str(required=True)


class ShopInfoSerializer(BaseSerializer):
    id = fields.Int(required=True)
    name = fields.Str(required=True)
