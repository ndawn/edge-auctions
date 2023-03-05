"""Adding push subscription model

Revision ID: eb6a727efb9e
Revises: 2fd6604d5f68
Create Date: 2023-02-18 18:02:30.872583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb6a727efb9e'
down_revision = '2fd6604d5f68'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('subscription_id', sa.String(length=255), nullable=False),
        sa.Column('data', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('push_subscriptions')
    # ### end Alembic commands ###
