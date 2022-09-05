"""Fixing external source enum

Revision ID: 4461db6f1d34
Revises: d45c5e0b954a
Create Date: 2022-08-05 17:27:41.766440

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4461db6f1d34'
down_revision = 'd45c5e0b954a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'external_entities',
        sa.Column('source', sa.Enum('VK', 'TELEGRAM', name='externalsource')),
    )


def downgrade() -> None:
    op.drop_column('external_entities', 'source')
