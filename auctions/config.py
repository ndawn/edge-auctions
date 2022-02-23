import os.path


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

DATABASE_URL = 'postgres://www:www@127.0.0.1:5432/auctions'
ORM_MODULES = {
    'accounts': ['auctions.accounts.models'],
    'ams': ['auctions.ams.models'],
    'auctioneer': ['auctions.auctioneer.models'],
    'comics': ['auctions.comics.models'],
    'supply': ['auctions.supply.models'],
}

TORTOISE_ORM = {
    'connections': {'default': DATABASE_URL},
    'apps': {
        app:
        {
            'models': app_config,
            'default_connection': 'default',
        }
        for app, app_config in ORM_MODULES.items()
    }
}

AWS_ACCESS_KEY_ID = 'AKIA3BLSMFREKUUQGA5C'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'edge-auctions'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_REGION_NAME = 'eu-north-1'

DEBUG = True

APP_URL = 'https://auctions.edgecomics.ru'
AMS_URL = 'https://ams.edgecomics.ru/api'
AMS_TOKEN = 'QAf0V-gi2OgZJnl5NjCUXwp2StFjceaHGpCxv20WbZxWtxiWlOexX5SaEggoOS-A'

AUCTION_CLOSE_LIMIT = 10
DEFAULT_TIMEZONE = 'Europe/Moscow'

IMAGE_TEMP_DIR = os.path.join(BASE_DIR, 'temp')
IMAGE_MIME_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
}
IMAGE_DEFAULT_MIME_TYPE = 'application/octet-stream'
IMAGE_IMAGES_DIR = 'images/'
IMAGE_THUMBS_DIR = 'thumbs/'
IMAGE_THUMB_BOUNDS = (350, 350)

SEPARATORS = {
    'storage': os.path.join(ASSETS_DIR, 'generated'),
    'text': os.path.join(ASSETS_DIR, 'text.png'),
    'start_price_position': (240, 370),
    'min_step_position': (1180, 370),
    'font': os.path.join(ASSETS_DIR, 'Calibri.ttf'),
    'variations': {
        650: os.path.join(ASSETS_DIR, 'purple.png'),
        350: os.path.join(ASSETS_DIR, 'blue.png'),
        300: os.path.join(ASSETS_DIR, 'lime.png'),
    },
}
