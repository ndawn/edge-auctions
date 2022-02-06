from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from auctions import config
from auctions.router import router


app = FastAPI()
app.include_router(router)
register_tortoise(
    app,
    db_url=config.DATABASE_URL,
    modules=config.ORM_MODULES,
    generate_schemas=True,
)

