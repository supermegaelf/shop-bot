"""Add referral tables

Revision ID: e166e15ef115
Revises: d82216707921
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'e166e15ef115'
down_revision = 'd82216707921'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('referrals',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('referrer_id', sa.BigInteger(), nullable=False),
    sa.Column('referred_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('referred_id')
    )
    op.create_index('ix_referrals_referrer_id', 'referrals', ['referrer_id'], unique=False)
    op.create_index('ix_referrals_referred_id', 'referrals', ['referred_id'], unique=False)
    
    op.create_table('referral_rewards',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('referrer_id', sa.BigInteger(), nullable=False),
    sa.Column('referred_id', sa.BigInteger(), nullable=False),
    sa.Column('payment_id', sa.String(length=64), nullable=False),
    sa.Column('reward_amount', sa.Integer(), nullable=False),
    sa.Column('reward_type', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('referrer_id', 'payment_id', name='uq_referrer_payment')
    )
    op.create_index('ix_referral_rewards_referrer_id', 'referral_rewards', ['referrer_id'], unique=False)
    op.create_index('ix_referral_rewards_referred_id', 'referral_rewards', ['referred_id'], unique=False)
    op.create_index('ix_referral_rewards_payment_id', 'referral_rewards', ['payment_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_referral_rewards_referred_id', table_name='referral_rewards')
    op.drop_index('ix_referral_rewards_referrer_id', table_name='referral_rewards')
    op.drop_table('referral_rewards')
    op.drop_index('ix_referrals_referred_id', table_name='referrals')
    op.drop_index('ix_referrals_referrer_id', table_name='referrals')
    op.drop_table('referrals')

