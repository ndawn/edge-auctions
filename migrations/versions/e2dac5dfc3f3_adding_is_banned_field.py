"""Adding is_banned field

Revision ID: e2dac5dfc3f3
Revises: 4bcadd0234be
Create Date: 2023-02-14 17:41:37.597211

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2dac5dfc3f3'
down_revision = '4bcadd0234be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), server_default='f', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column('users', 'is_banned')
