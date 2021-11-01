import os.path
from uuid import uuid4

from fastapi import UploadFile
from fastapi.exceptions import HTTPException
from PIL import Image as PillowImage
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from auctions.config import (
    IMAGE_DEFAULT_MIME_TYPE,
    IMAGE_IMAGES_DIR,
    IMAGE_MIME_TYPES,
    IMAGE_TEMP_DIR,
    IMAGE_THUMB_BOUNDS,
    IMAGE_THUMBS_DIR,
)
from auctions.supply.models import SupplyImage, SupplyItem
from auctions.utils.barcode import scan_barcode
from auctions.utils.s3 import S3ImageUploader


S3 = S3ImageUploader()


async def process_image(file: UploadFile) -> tuple[SupplyImage, SupplyItem]:
    file_extension = file.filename.rsplit('.', 1)[-1]
    file_mime = IMAGE_MIME_TYPES.get(file_extension, IMAGE_DEFAULT_MIME_TYPE)

    object_name = str(uuid4())
    object_path = os.path.join(IMAGE_IMAGES_DIR, object_name)
    thumb_path = os.path.join(IMAGE_THUMBS_DIR, object_name)

    object_temp_path = os.path.join(IMAGE_TEMP_DIR, f'{object_name}.{file_extension}')
    thumb_temp_path = os.path.join(IMAGE_TEMP_DIR, f'{object_name}.thumb.{file_extension}')

    with open(object_temp_path, 'wb') as temp_file:
        temp_file.write(await file.read())

    thumb: PillowImage.Image = PillowImage.open(object_temp_path)
    thumb.thumbnail(IMAGE_THUMB_BOUNDS, PillowImage.ANTIALIAS)
    thumb.save(thumb_temp_path)

    try:
        await S3.upload_image(
            file_path=object_temp_path,
            object_name=object_path,
            extra_args={'ContentType': file_mime},
        )
        await S3.upload_image(
            file_path=thumb_temp_path,
            object_name=thumb_path,
            extra_args={'ContentType': file_mime},
        )
    except S3.throws as exception:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error occurred while uploading the file: {str(exception)}',
        )

    upca, upc5 = scan_barcode(PillowImage.open(object_temp_path))

    db_item = await SupplyItem.create(
        upca=upca,
        upc5=upc5,
    )

    db_image = await SupplyImage.create(
        uuid=object_name,
        extension=file_extension,
        image_url=S3.get_image_url(object_path),
        thumb_url=S3.get_image_url(thumb_path),
        is_main=True,
    )

    return db_image, db_item
