from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class MiniappLoginSerializer(BaseSerializer):
    vk_user_id = fields.Str(required=True)
    vk_app_id = fields.Str(required=True)
    vk_is_app_user = fields.Str(required=False)
    vk_are_notifications_enabled = fields.Str(required=False)
    vk_language = fields.Str(required=False)
    vk_ref = fields.Str(required=False)
    vk_access_token_settings = fields.Str(required=False)
    vk_group_id = fields.Str(required=False)
    vk_viewer_group_role = fields.Str(required=False)
    vk_platform = fields.Str(required=False)
    vk_is_favorite = fields.Str(required=False)
    vk_ts = fields.Str(required=False)
    vk_is_recommended = fields.Str(required=False)
    vk_profile_id = fields.Str(required=False)
    sign = fields.Str(required=True)
    odr_enabled = fields.Str(required=False)
