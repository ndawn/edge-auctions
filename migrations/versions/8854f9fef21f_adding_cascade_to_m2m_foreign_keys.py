"""Adding cascade to m2m foreign keys

Revision ID: 8854f9fef21f
Revises: 4461db6f1d34
Create Date: 2022-08-06 13:41:37.020760

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8854f9fef21f'
down_revision = '4461db6f1d34'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        'auction_sets_external_entities_entity_id_fkey',
        'auction_sets_external_entities',
        type_='foreignkey',
    )
    op.drop_constraint(
        'auction_targets_external_entities_entity_id_fkey',
        'auction_targets_external_entities',
        type_='foreignkey',
    )
    op.drop_constraint(
        'auctions_external_entities_entity_id_fkey',
        'auctions_external_entities',
        type_='foreignkey',
    )
    op.drop_constraint(
        'bidders_external_entities_entity_id_fkey',
        'bidders_external_entities',
        type_='foreignkey',
    )

    op.create_foreign_key(
        'auction_sets_external_entities_entity_id_fkey',
        'auction_sets_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'auction_targets_external_entities_entity_id_fkey',
        'auction_targets_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'auctions_external_entities_entity_id_fkey',
        'auctions_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'bidders_external_entities_entity_id_fkey',
        'bidders_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint(
        'auction_sets_external_entities_entity_id_fkey',
        'auction_sets_external_entities',
        type_='foreignkey',
    )
    op.drop_constraint(
        'auction_targets_external_entities_entity_id_fkey',
        'auction_targets_external_entities',
        type_='foreignkey',
    )
    op.drop_constraint(
        'auctions_external_entities_entity_id_fkey',
        'auctions_external_entities',
        type_='foreignkey',
    )
    op.drop_constraint(
        'bidders_external_entities_entity_id_fkey',
        'bidders_external_entities',
        type_='foreignkey',
    )

    op.create_foreign_key(
        'auction_sets_external_entities_entity_id_fkey',
        'auction_sets_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
    )
    op.create_foreign_key(
        'auction_targets_external_entities_entity_id_fkey',
        'auction_targets_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
    )
    op.create_foreign_key(
        'auctions_external_entities_entity_id_fkey',
        'auctions_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
    )
    op.create_foreign_key(
        'bidders_external_entities_entity_id_fkey',
        'bidders_external_entities',
        'external_entities',
        ['entity_id'],
        ['id'],
    )
