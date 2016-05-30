"""Add vparturl column

Revision ID: 36c23e6c0183
Revises: 65c192261da
Create Date: 2016-05-30 05:54:01.945979

"""

# revision identifiers, used by Alembic.
revision = '36c23e6c0183'
down_revision = '65c192261da'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('VendorPartDetail', sa.Column('vparturl', sa.String, nullable=True, unique=False))


def downgrade():
    op.drop_column('VendorPartDetail', 'vparturl')
