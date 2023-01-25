from datetime import datetime
from datetime import timezone

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db


class ShopInfo(db.Model):
    __tablename__ = "shop_info"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(255), unique=True)
    password: Mapped[str | None] = db.Column(db.String(32), nullable=True)
