"""notifications: sender_id (hereglegch hoorondiin zahidal)

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('notif_notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sender_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_notif_notifications_sender_id'), ['sender_id'], unique=False)
        batch_op.create_foreign_key('fk_notif_notifications_sender_id_auth_users',
                                    'auth_users', ['sender_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('notif_notifications', schema=None) as batch_op:
        batch_op.drop_constraint('fk_notif_notifications_sender_id_auth_users', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_notif_notifications_sender_id'))
        batch_op.drop_column('sender_id')
