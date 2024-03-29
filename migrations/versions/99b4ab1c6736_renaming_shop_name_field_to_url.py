"""Renaming shop name field to url

Revision ID: 99b4ab1c6736
Revises: 81d5633a3972
Create Date: 2023-02-15 16:56:13.435903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99b4ab1c6736'
down_revision = '81d5633a3972'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shop_info', sa.Column('url', sa.String(length=255), nullable=True))
    op.drop_constraint('shop_info_name_key', 'shop_info', type_='unique')
    op.create_unique_constraint(None, 'shop_info', ['url'])
    op.drop_column('shop_info', 'name')
    op.add_column('users', sa.Column('shop_id', sa.Integer(), nullable=True))
    op.create_unique_constraint(None, 'users', ['shop_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'shop_id')
    op.add_column('shop_info', sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'shop_info', type_='unique')
    op.create_unique_constraint('shop_info_name_key', 'shop_info', ['name'])
    op.drop_column('shop_info', 'url')
    # ### end Alembic commands ###
