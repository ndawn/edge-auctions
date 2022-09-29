from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.images import Image
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.images import ImageSerializer
from auctions.services.images_service import ImagesService
from auctions.utils.error_handler import with_error_handler
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=Image,
    serializer_name="image_serializer",
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    create_args=ImageSerializer(),
    update_args=ImageSerializer(partial=True),
    operations=('update', 'delete'),
)


@blueprint.post("/bulk_create")
@with_error_handler
@login_required()
@inject
def bulk_create(
    images_service: ImagesService = Provide["images_service"],
    image_serializer: ImageSerializer = Provide["image_serializer"],
) -> JsonResponse:
    args = parser.parse(
        {
            "images": fields.List(fields.Field(), required=True),
        },
        request,
        location="files",
    )

    images = images_service.bulk_upload(args["images"])
    return JsonResponse(image_serializer.dump(images, many=True))
