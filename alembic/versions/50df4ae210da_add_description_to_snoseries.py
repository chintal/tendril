"""Add description to snoseries

Revision ID: 50df4ae210da
Revises: 205d6ab2febf
Create Date: 2016-01-03 23:32:11.184463

"""

# revision identifiers, used by Alembic.
revision = '50df4ae210da'
down_revision = '205d6ab2febf'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('SerialNumberSeries', sa.Column('description', sa.String, unique=False, nullable=True))


def downgrade():
    op.drop_column('SerialNumberSeries', sa.Column('description', sa.String, unique=False, nullable=True))
