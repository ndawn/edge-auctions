"""Removing length restriction on upc fields

Revision ID: 4bcadd0234be
Revises: 2e99669e439c
Create Date: 2023-02-05 22:42:54.344617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4bcadd0234be"
down_revision = "2e99669e439c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "items",
        "upca",
        existing_type=sa.VARCHAR(length=12),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
    op.alter_column(
        "items",
        "upc5",
        existing_type=sa.VARCHAR(length=5),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "items",
        "upca",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.String(length=12),
        existing_nullable=True,
    )
    op.alter_column(
        "items",
        "upc5",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.String(length=5),
        existing_nullable=True,
    )
