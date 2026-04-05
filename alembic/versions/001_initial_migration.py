"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-03-31 16:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Создание таблицы events
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('date_start', sa.DateTime(), nullable=False),
        sa.Column('date_end', sa.DateTime(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('is_moderated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_category'), 'events', ['category'], unique=False)
    op.create_index(op.f('ix_events_date_start'), 'events', ['date_start'], unique=False)
    op.create_index(op.f('ix_events_is_published'), 'events', ['is_published'], unique=False)

    # Создание таблицы user_settings
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notify_new_events', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_friend_going', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_event_reminder', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('preferred_categories', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_settings_user_id'), 'user_settings', ['user_id'], unique=True)

    # Создание таблицы friendships
    op.create_table(
        'friendships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='unique_friendship')
    )
    op.create_index(op.f('ix_friendships_user_id'), 'friendships', ['user_id'], unique=False)
    op.create_index(op.f('ix_friendships_friend_id'), 'friendships', ['friend_id'], unique=False)

    # Создание таблицы event_attendances
    op.create_table(
        'event_attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='going'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'event_id', name='unique_attendance')
    )
    op.create_index(op.f('ix_event_attendances_user_id'), 'event_attendances', ['user_id'], unique=False)
    op.create_index(op.f('ix_event_attendances_event_id'), 'event_attendances', ['event_id'], unique=False)

    # Создание таблицы notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('related_event_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_event_id'], ['events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)

    # Создание таблицы event_sources
    op.create_table(
        'event_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('parser_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_parsed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('event_sources')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_event_attendances_event_id'), table_name='event_attendances')
    op.drop_index(op.f('ix_event_attendances_user_id'), table_name='event_attendances')
    op.drop_table('event_attendances')
    op.drop_index(op.f('ix_friendships_friend_id'), table_name='friendships')
    op.drop_index(op.f('ix_friendships_user_id'), table_name='friendships')
    op.drop_table('friendships')
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_table('user_settings')
    op.drop_index(op.f('ix_events_is_published'), table_name='events')
    op.drop_index(op.f('ix_events_date_start'), table_name='events')
    op.drop_index(op.f('ix_events_category'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
