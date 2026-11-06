"""auth: customer_id ("Hereglegch" uureg hariltsagchtai holbogdono - portal)

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('auth_users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_auth_users_customer_id'), ['customer_id'], unique=False)
        batch_op.create_foreign_key('fk_auth_users_customer_id_md_customers', 'md_customers',
                                    ['customer_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('auth_users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_auth_users_customer_id_md_customers', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_auth_users_customer_id'))
        batch_op.drop_column('customer_id')
