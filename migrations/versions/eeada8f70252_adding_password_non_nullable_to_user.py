"""Adding password non nullable to user

Revision ID: eeada8f70252
Revises: e7ef1b78a563
Create Date: 2023-02-15 18:44:40.194243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eeada8f70252'
down_revision = 'e7ef1b78a563'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=512),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=512),
               nullable=True)
    # ### end Alembic commands ###
