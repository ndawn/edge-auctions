from sqlalchemy.orm.attributes import Mapped

from auctions.db import db


class Template(db.Model):
    __tablename__ = "templates"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    alias: Mapped[str] = db.Column(db.String(255))
    text: Mapped[str] = db.Column(db.Text, default="")
