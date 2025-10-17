"""add message_id to payments

Revision ID: 6051f2ee522f
Revises: d82216707921
Create Date: 2025-10-17 01:40:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6051f2ee522f'
down_revision = 'd82216707921'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('message_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('payments', 'message_id')
