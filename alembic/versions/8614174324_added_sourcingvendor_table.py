"""Added SourcingVendor table

Revision ID: 8614174324
Revises: 50df4ae210da
Create Date: 2016-01-05 22:52:06.415691

"""

# revision identifiers, used by Alembic.
revision = '8614174324'
down_revision = '50df4ae210da'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('SourcingVendor',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('dname', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('mapfile_base', sa.String(), nullable=False),
    sa.Column('pclass_str', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('mapfile_base'),
    sa.UniqueConstraint('name')
    )


def downgrade():
    op.drop_table('SourcingVendor')
