import os.path


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = 'postgres://www:www@127.0.0.1:5432/auctions'

AWS_ACCESS_KEY_ID = 'AKIA3BLSMFREKUUQGA5C'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'edge-auctions'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_REGION_NAME = 'eu-north-1'

AMS_URL = 'https://ams.edgecomics.ru'

AUCTION_CLOSE_LIMIT = 10

IMAGE_TEMP_DIR = os.path.join(BASE_DIR, 'temp')
IMAGE_MIME_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
}
IMAGE_DEFAULT_MIME_TYPE = 'application/octet-stream'
IMAGE_IMAGES_DIR = 'images/'
IMAGE_THUMBS_DIR = 'thumbs/'
IMAGE_THUMB_BOUNDS = (350, 350)
