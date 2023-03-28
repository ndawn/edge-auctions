"""Altering push_subscription model

Revision ID: 6f209058e12d
Revises: d28c86e3d9b2
Create Date: 2023-03-26 23:55:38.775143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f209058e12d'
down_revision = 'd28c86e3d9b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('push_subscriptions', sa.Column('token', sa.String(), nullable=False))
    op.drop_constraint('push_subscriptions_endpoint_key', 'push_subscriptions', type_='unique')
    op.create_unique_constraint(None, 'push_subscriptions', ['token'])
    op.drop_column('push_subscriptions', 'endpoint')
    op.drop_column('push_subscriptions', 'data')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('push_subscriptions', sa.Column('data', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column('push_subscriptions', sa.Column('endpoint', sa.TEXT(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'push_subscriptions', type_='unique')
    op.create_unique_constraint('push_subscriptions_endpoint_key', 'push_subscriptions', ['endpoint'])
    op.drop_column('push_subscriptions', 'token')
    # ### end Alembic commands ###