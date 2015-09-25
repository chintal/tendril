"""create_sno_series_table

Revision ID: 205d6ab2febf
Revises: 1f03af77d718
Create Date: 2015-09-25 10:55:07.669159

"""

# revision identifiers, used by Alembic.
revision = '205d6ab2febf'
down_revision = '1f03af77d718'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'SerialNumberSeries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('series', sa.String, nullable=False, unique=True),
        sa.Column('last_seed', sa.String, nullable=False, unique=False)
    )


def downgrade():
    op.drop_Table(
        'SerialNumberSeries'
    )
