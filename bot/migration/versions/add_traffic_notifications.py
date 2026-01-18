"""Add traffic notifications table

Revision ID: 8b4c5d6e7f89
Revises: 7a3c4d5e6f78
Create Date: 2026-01-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '8b4c5d6e7f89'
down_revision = '7a3c4d5e6f78'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'traffic_notifications' not in tables:
        op.create_table('traffic_notifications',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_traffic_notifications_tg_id', 'traffic_notifications', ['tg_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_traffic_notifications_tg_id', table_name='traffic_notifications')
    op.drop_table('traffic_notifications')
