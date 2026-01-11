"""Add referral system

Revision ID: add_referral_system
Revises: e9f8a7b6c5d4
Create Date: 2026-01-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_referral_system'
down_revision = 'e9f8a7b6c5d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('vpnusers')]
    indexes = [idx['name'] for idx in inspector.get_indexes('vpnusers')]
    
    if 'referral_code' not in columns:
        op.add_column('vpnusers', sa.Column('referral_code', sa.String(length=16), nullable=True))
    
    if 'referred_by_id' not in columns:
        op.add_column('vpnusers', sa.Column('referred_by_id', sa.BigInteger(), nullable=True))
    
    if 'ix_vpnusers_tg_id' not in indexes:
        op.create_index('ix_vpnusers_tg_id', 'vpnusers', ['tg_id'], unique=True)
    
    if 'ix_vpnusers_referral_code' not in indexes:
        op.create_index('ix_vpnusers_referral_code', 'vpnusers', ['referral_code'], unique=True)
    
    try:
        op.create_foreign_key('fk_vpnusers_referred_by', 'vpnusers', 'vpnusers', ['referred_by_id'], ['tg_id'])
    except:
        pass
    
    tables = inspector.get_table_names()
    if 'referral_bonuses' not in tables:
        op.create_table('referral_bonuses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('inviter_id', sa.BigInteger(), nullable=False),
        sa.Column('referee_id', sa.BigInteger(), nullable=False),
        sa.Column('payment_id', sa.BigInteger(), nullable=True),
        sa.Column('bonus_days_inviter', sa.Integer(), nullable=False),
        sa.Column('bonus_days_referee', sa.Integer(), nullable=False),
        sa.Column('purchase_days', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    op.drop_table('referral_bonuses')
    op.drop_constraint('fk_vpnusers_referred_by', 'vpnusers', type_='foreignkey')
    op.drop_index('ix_vpnusers_referral_code', table_name='vpnusers')
    op.drop_index('ix_vpnusers_tg_id', table_name='vpnusers')
    op.drop_column('vpnusers', 'referred_by_id')
    op.drop_column('vpnusers', 'referral_code')
