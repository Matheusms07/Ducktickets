"""Add coupons and requires_coupon field

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add requires_coupon field to ticket_batches
    op.add_column('ticket_batches', sa.Column('requires_coupon', sa.Boolean(), default=False))
    
    # Create coupons table
    op.create_table('coupons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('ticket_batch_id', sa.Integer(), nullable=False),
        sa.Column('discount_percent', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('discount_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ticket_batch_id'], ['ticket_batches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coupons_code'), 'coupons', ['code'], unique=True)
    op.create_index(op.f('ix_coupons_id'), 'coupons', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_coupons_id'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_code'), table_name='coupons')
    op.drop_table('coupons')
    op.drop_column('ticket_batches', 'requires_coupon')