import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from auctions.db import db
from auctions.db.models.auction_sets import AuctionSet_ExternalEntity
from auctions.db.models.auction_targets import AuctionTarget
from auctions.db.models.auction_targets import AuctionTarget_ExternalEntity
from auctions.db.models.auctions import Auction
from auctions.db.models.auctions import Auction_ExternalEntity
from auctions.db.models.bidders import Bidder
from auctions.db.models.bidders import Bidder_ExternalEntity
from auctions.db.models.bids import Bid
from auctions.db.models.external import ExternalEntity
from auctions.db.models.images import Image
from auctions.db.models.item_types import ItemType
from auctions.db.models.items import Item
from auctions.db.models.price_categories import PriceCategory
from auctions.db.models.sessions import SupplySession
from auctions.db.models.templates import Template
from auctions.db.models.users import AuthToken
from auctions.db.models.users import User

target_metadata = db.Model.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url", os.getenv("DB_URL"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()