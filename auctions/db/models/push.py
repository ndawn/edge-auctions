from typing import TYPE_CHECKING

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.users import User


class PushSubscription(db.Model):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = db.Column(db.String(255), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = db.relationship(
        "User",
        foreign_keys="PushSubscription.user_id",
        back_populates="subscriptions",
    )
    endpoint: Mapped[str] = db.Column(db.Text(), unique=True, nullable=False)
    data: Mapped[str] = db.Column(db.Text(), nullable=False)
