from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.bids import Bid
    from auctions.db.models.push import PushSubscription


class User(Model):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    shop_id: Mapped[int]
    email: Mapped[str] = mapped_column(unique=True)
    phone: Mapped[str]
    address: Mapped[str]
    password: Mapped[str]
    first_name: Mapped[str] = mapped_column(default="")
    last_name: Mapped[str] = mapped_column(default="")
    full_name: Mapped[str] = mapped_column(default="")
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_banned: Mapped[bool] = mapped_column(default=False)

    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="user")
    subscriptions: Mapped[list["PushSubscription"]] = relationship("PushSubscription", back_populates="user")
