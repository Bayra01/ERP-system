"""auth: pending (uuriigee burtguulsen, admin batlaagui)

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('auth_users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pending', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('auth_users', schema=None) as batch_op:
        batch_op.drop_column('pending')
