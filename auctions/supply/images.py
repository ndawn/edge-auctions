from io import BytesIO
import os.path
import uuid

from exif import Image as ExifImage
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
from auctions.supply.models import SupplyImage, SupplyItem, SupplyItemParseStatus, SupplySession
from auctions.utils.barcode import scan_barcode
from auctions.utils.s3 import S3ImageUploader


S3 = S3ImageUploader()


async def create_item_from_image(file: UploadFile, session: SupplySession) -> SupplyItem:
    file_extension = file.filename.rsplit('.', 1)[-1]
    file_mime = IMAGE_MIME_TYPES.get(file_extension.lower(), IMAGE_DEFAULT_MIME_TYPE)

    object_name = str(uuid.uuid4())
    object_path = os.path.join(IMAGE_IMAGES_DIR, object_name)
    thumb_path = os.path.join(IMAGE_THUMBS_DIR, object_name)

    object_temp_path = os.path.join(IMAGE_TEMP_DIR, f'{object_name}.{file_extension}')
    thumb_temp_path = os.path.join(IMAGE_TEMP_DIR, f'{object_name}.thumb.{file_extension}')

    file_raw = BytesIO(await file.read())
    exif_data = ExifImage(file_raw)
    exif_orientation = exif_data.get('orientation', 1)
    exif_data['orientation'] = 1

    file_raw = BytesIO(exif_data.get_file())

    if exif_orientation != 1:
        image_data = PillowImage.open(file_raw)
        rotation = None
        bounds = None
        if exif_orientation == 8:
            rotation = PillowImage.ROTATE_90
            bounds = tuple(reversed(image_data.size))
        elif exif_orientation == 3:
            rotation = PillowImage.ROTATE_180
            bounds = image_data.size
        elif exif_orientation == 6:
            rotation = PillowImage.ROTATE_270
            bounds = tuple(reversed(image_data.size))

        rotated_image = PillowImage.new('RGB', bounds)
        rotated_image.paste(image_data.transpose(rotation))
        rotated_image.save(object_temp_path)

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

    os.remove(object_temp_path)
    os.remove(thumb_temp_path)

    db_item = await SupplyItem.create(
        uuid=uuid.uuid4(),
        parse_status=SupplyItemParseStatus.PENDING if upca and upc5 else SupplyItemParseStatus.FAILED,
        session=session,
        price_category=session.item_type.price_category,
        wrap_to=session.item_type.template_wrap_to,
        upca=upca,
        upc5=upc5,
    )

    await SupplyImage.create(
        uuid=object_name,
        extension=file_extension,
        image_url=S3.get_image_url(object_path),
        thumb_url=S3.get_image_url(thumb_path),
        item=db_item,
        is_main=True,
    )

    return db_item


async def delete_image_from_s3(image: SupplyImage):
    try:
        await S3.delete_image(os.path.join(IMAGE_IMAGES_DIR, str(image.uuid)))
        await S3.delete_image(os.path.join(IMAGE_THUMBS_DIR, str(image.uuid)))
    except S3.throws as exception:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error occurred while deleting the file: {str(exception)}',
        )
