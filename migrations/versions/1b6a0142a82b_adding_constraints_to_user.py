"""Adding constraints to user

Revision ID: 1b6a0142a82b
Revises: 4974d4dcd238
Create Date: 2023-02-15 18:28:31.115368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b6a0142a82b'
down_revision = '4974d4dcd238'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'shop_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.create_unique_constraint(None, 'users', ['shop_id'])
    op.create_unique_constraint(None, 'users', ['email'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('users', 'shop_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###