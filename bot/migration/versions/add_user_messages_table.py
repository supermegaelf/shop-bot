"""Add user messages table

Revision ID: 9c5d6e7f8a90
Revises: 8b4c5d6e7f89
Create Date: 2026-01-18 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '9c5d6e7f8a90'
down_revision = '8b4c5d6e7f89'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'user_messages' not in tables:
        op.create_table('user_messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_user_messages_tg_id', 'user_messages', ['tg_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_user_messages_tg_id', table_name='user_messages')
    op.drop_table('user_messages')
