"""Update users table for authentication

Revision ID: 003
Revises: 002
Create Date: 2025-08-17 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing users table and recreate with new structure
    op.drop_table('users')
    
    # Create new users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

def downgrade():
    # Revert to original users table structure
    op.drop_table('users')
    
    op.create_table('users',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)