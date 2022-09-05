"""Initial migration

Revision ID: 9c2a7e970e1a
Revises: 
Create Date: 2022-07-13 04:43:26.905733

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9c2a7e970e1a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('auction_targets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('external_entities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source', sa.Enum('VK', 'TELEGRAM', name='externalsource'), nullable=True),
    sa.Column('entity_id', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('entity_id')
    )
    op.create_table('price_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('alias', sa.String(length=255), nullable=True),
    sa.Column('usd', sa.Float(), nullable=True),
    sa.Column('rub', sa.Integer(), nullable=True),
    sa.Column('buy_now_price', sa.Integer(), nullable=True),
    sa.Column('buy_now_expires', sa.Integer(), nullable=True),
    sa.Column('bid_start_price', sa.Integer(), nullable=True),
    sa.Column('bid_min_step', sa.Integer(), nullable=True),
    sa.Column('bid_multiple_of', sa.Integer(), nullable=True),
    sa.Column('manual', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('templates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('alias', sa.String(length=255), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('first_name', sa.String(length=255), nullable=True),
    sa.Column('last_name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('auction_sets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('date_due', sa.DateTime(timezone=True), nullable=True),
    sa.Column('anti_sniper', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['target_id'], ['auction_targets.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auction_targets_external_entities',
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['entity_id'], ['external_entities.id'], ),
    sa.ForeignKeyConstraint(['target_id'], ['auction_targets.id'], )
    )
    op.create_table('auth_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('token', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bidders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('last_name', sa.String(length=255), nullable=True),
    sa.Column('first_name', sa.String(length=255), nullable=True),
    sa.Column('avatar', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['target_id'], ['auction_targets.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('item_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('price_category_id', sa.Integer(), nullable=True),
    sa.Column('wrap_to_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['price_category_id'], ['price_categories.id'], ),
    sa.ForeignKeyConstraint(['wrap_to_id'], ['templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auction_sets_external_entities',
    sa.Column('set_id', sa.Integer(), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['entity_id'], ['external_entities.id'], ),
    sa.ForeignKeyConstraint(['set_id'], ['auction_sets.id'], )
    )
    op.create_table('bidders_external_entities',
    sa.Column('bidder_id', sa.Integer(), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['bidder_id'], ['bidders.id'], ),
    sa.ForeignKeyConstraint(['entity_id'], ['external_entities.id'], )
    )
    op.create_table('supply_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('item_type_id', sa.Integer(), nullable=True),
    sa.Column('total_items', sa.Integer(), nullable=True),
    sa.Column('uploaded_items', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_type_id'], ['item_types.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('wrap_to_id', sa.Integer(), nullable=True),
    sa.Column('type_id', sa.Integer(), nullable=True),
    sa.Column('upca', sa.String(length=12), nullable=True),
    sa.Column('upc5', sa.String(length=5), nullable=True),
    sa.Column('price_category_id', sa.Integer(), nullable=True),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.Column('parse_status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', name='supplyitemparsestatus'), nullable=True),
    sa.Column('parse_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.ForeignKeyConstraint(['price_category_id'], ['price_categories.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['supply_sessions.id'], ),
    sa.ForeignKeyConstraint(['type_id'], ['item_types.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['wrap_to_id'], ['templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auctions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('set_id', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('date_due', sa.DateTime(timezone=True), nullable=True),
    sa.Column('buy_now_price', sa.Integer(), nullable=True),
    sa.Column('buy_now_expires', sa.Integer(), nullable=True),
    sa.Column('bid_start_price', sa.Integer(), nullable=True),
    sa.Column('bid_min_step', sa.Integer(), nullable=True),
    sa.Column('bid_multiple_of', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['set_id'], ['auction_sets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('extension', sa.String(length=8), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('image_url', sa.String(length=512), nullable=True),
    sa.Column('thumb_url', sa.String(length=512), nullable=True),
    sa.Column('is_main', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auctions_external_entities',
    sa.Column('auction_id', sa.Integer(), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['auction_id'], ['auctions.id'], ),
    sa.ForeignKeyConstraint(['entity_id'], ['external_entities.id'], )
    )
    op.create_table('bids',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bidder_id', sa.Integer(), nullable=True),
    sa.Column('auction_id', sa.Integer(), nullable=True),
    sa.Column('value', sa.Integer(), nullable=True),
    sa.Column('is_sniped', sa.Boolean(), nullable=True),
    sa.Column('is_buyout', sa.Boolean(), nullable=True),
    sa.Column('next_bid_id', sa.Integer(), nullable=True),
    sa.Column('external_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['auction_id'], ['auctions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['bidder_id'], ['bidders.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['external_id'], ['external_entities.id'], ),
    sa.ForeignKeyConstraint(['next_bid_id'], ['bids.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bids_external_entities',
    sa.Column('bid_id', sa.Integer(), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
    sa.ForeignKeyConstraint(['entity_id'], ['external_entities.id'], )
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('bids_external_entities')
    op.drop_table('bids')
    op.drop_table('auctions_external_entities')
    op.drop_table('images')
    op.drop_table('auctions')
    op.drop_table('items')
    op.drop_table('supply_sessions')
    op.drop_table('bidders_external_entities')
    op.drop_table('auction_sets_external_entities')
    op.drop_table('item_types')
    op.drop_table('bidders')
    op.drop_table('auth_tokens')
    op.drop_table('auction_targets_external_entities')
    op.drop_table('auction_sets')
    op.drop_table('users')
    op.drop_table('templates')
    op.drop_table('price_categories')
    op.drop_table('external_entities')
    op.drop_table('auction_targets')
    # ### end Alembic commands ###