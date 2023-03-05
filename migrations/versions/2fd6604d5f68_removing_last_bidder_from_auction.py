"""Removing last_bidder from auction

Revision ID: 2fd6604d5f68
Revises: c32373e9d323
Create Date: 2023-02-17 22:25:17.877829

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2fd6604d5f68'
down_revision = 'c32373e9d323'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('auctions_last_bidder_id_fkey', 'auctions', type_='foreignkey')
    op.drop_column('auctions', 'last_bidder_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('auctions', sa.Column('last_bidder_id', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.create_foreign_key('auctions_last_bidder_id_fkey', 'auctions', 'users', ['last_bidder_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###
