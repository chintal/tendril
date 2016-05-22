"""Changed VendorElnPartDetail columns to Nullable

Revision ID: 65c192261da
Revises: 12a02ab56b86
Create Date: 2016-05-22 05:19:58.793471

"""

# revision identifiers, used by Alembic.
revision = '65c192261da'
down_revision = '12a02ab56b86'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('VendorElnPartDetail', 'package', nullable=True)
    op.alter_column('VendorElnPartDetail', 'datasheet', nullable=True)


def downgrade():
    op.alter_column('VendorElnPartDetail', 'package', nullable=False)
    op.alter_column('VendorElnPartDetail', 'datasheet', nullable=False)
