from flask import request
from webargs import fields
from webargs.flaskparser import parser

from auctions.db.models.images import Image
from auctions.dependencies import Provide
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.images import ImageSerializer
from auctions.services.images_service import ImagesService
from auctions.utils.endpoints import endpoint
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=Image,
    serializer_class=ImageSerializer,
    list_args={
        "page": fields.Int(required=False, default=0),
        "page_size": fields.Int(required=False, default=50),
    },
    create_args=ImageSerializer(),
    update_args=ImageSerializer(partial=True),
    operations={'update', 'delete'},
)


@endpoint(blueprint.post("/bulk_create"))
def bulk_create(
    images_service: ImagesService = Provide(),
    image_serializer: ImageSerializer = Provide(),
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
