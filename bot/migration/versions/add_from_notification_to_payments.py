"""add from_notification to payments

Revision ID: 7a3c4d5e6f78
Revises: 6051f2ee522f
Create Date: 2025-10-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a3c4d5e6f78'
down_revision = '6051f2ee522f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('from_notification', sa.Boolean(), nullable=True, default=False))


def downgrade() -> None:
    op.drop_column('payments', 'from_notification')
