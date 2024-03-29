"""Removing fields

Revision ID: 19b843b6344d
Revises: 0d1278b77dcc
Create Date: 2023-03-03 23:17:56.125380

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '19b843b6344d'
down_revision = '0d1278b77dcc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.drop_column('users', 'last_prompted_for_address_at')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('last_prompted_for_address_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'address')
    # ### end Alembic commands ###
