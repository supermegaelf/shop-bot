"""Merge referral system and user messages

Revision ID: f1a2b3c4d5e6
Revises: add_referral_system, 9c5d6e7f8a90
Create Date: 2026-02-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a2b3c4d5e6'
down_revision = ('add_referral_system', '9c5d6e7f8a90')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
