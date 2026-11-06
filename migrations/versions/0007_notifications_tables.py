"""notifications tables

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('notif_notifications',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event', sa.String(length=60), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=True),
    sa.Column('data', sa.JSON(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('notif_notifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notif_notifications_event'), ['event'], unique=False)
        batch_op.create_index(batch_op.f('ix_notif_notifications_is_read'), ['is_read'], unique=False)
        batch_op.create_index(batch_op.f('ix_notif_notifications_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('notif_notifications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notif_notifications_user_id'))
        batch_op.drop_index(batch_op.f('ix_notif_notifications_is_read'))
        batch_op.drop_index(batch_op.f('ix_notif_notifications_event'))
    op.drop_table('notif_notifications')
