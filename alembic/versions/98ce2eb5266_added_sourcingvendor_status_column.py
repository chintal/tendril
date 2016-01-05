"""Added SourcingVendor status column

Revision ID: 98ce2eb5266
Revises: 8614174324
Create Date: 2016-01-05 23:03:22.032600

"""

# revision identifiers, used by Alembic.
revision = '98ce2eb5266'
down_revision = '8614174324'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('SourcingVendor',
                  sa.Column('status',
                            sa.Enum('active', 'suspended', 'defunct', name='vendor_status'),
                            server_default='active',
                            default='active',
                            nullable=False)
                  )


def downgrade():
    op.drop_column('SourcingVendor', 'status')
