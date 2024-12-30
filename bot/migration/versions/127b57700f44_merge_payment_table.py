"""Merge payment table

Revision ID: 127b57700f44
Revises: 36159a9e6985
Create Date: 2024-12-03 18:44:37.175247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '127b57700f44'
down_revision = '36159a9e6985'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('payments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=True),
    sa.Column('lang', sa.String(length=64), nullable=True),
    sa.Column('payment_id', sa.String(length=128), nullable=True),
    sa.Column('type', sa.Integer(), nullable=True),
    sa.Column('callback', sa.String(length=64), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.drop_table('crypto_payments')
    op.drop_table('yookassa_payments')
    pass


def downgrade() -> None:
    op.create_table('crypto_payments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=True),
    sa.Column('lang', sa.String(length=64), nullable=True),
    sa.Column('payment_uuid', sa.String(length=64), nullable=True),
    sa.Column('order_id', sa.String(length=64), nullable=True),
    sa.Column('chat_id', sa.BigInteger(), nullable=True),
    sa.Column('callback', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('yookassa_payments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=True),
    sa.Column('lang', sa.String(length=64), nullable=True),
    sa.Column('payment_id', sa.String(length=64), nullable=True),
    sa.Column('chat_id', sa.BigInteger(), nullable=True),
    sa.Column('callback', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.drop_table('payments')
    pass
