from webargs import fields

from auctions.db.models.templates import Template
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.templates import TemplateSerializer

blueprint = create_crud_blueprint(
    model=Template,
    serializer_name="template_serializer",
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=20),
    },
    create_args=TemplateSerializer(),
    update_args=TemplateSerializer(partial=True),
)
