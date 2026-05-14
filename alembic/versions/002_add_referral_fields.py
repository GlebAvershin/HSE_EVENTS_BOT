"""Add referral fields to users

Revision ID: 002
Revises: 001
Create Date: 2026-04-27 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('referral_code', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('referred_by', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_column('users', 'referred_by')
    op.drop_column('users', 'referral_code')
