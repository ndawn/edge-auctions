from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model


class Template(Model):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    alias: Mapped[str]
    text: Mapped[str] = mapped_column(default="")
