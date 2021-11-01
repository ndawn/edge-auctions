from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from auctions import config
from auctions.router import router


app = FastAPI()
app.include_router(router)
register_tortoise(
    app,
    db_url=config.DATABASE_URL,
    modules={
        'accounts': ['auctions.accounts.models'],
        'ams': ['auctions.ams.models'],
        'auctioneer': ['auctions.auctioneer.models'],
        'comics': ['auctions.comics.models'],
        'supply': ['auctions.supply.models'],
    },
    generate_schemas=True,
)

