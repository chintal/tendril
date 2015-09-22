"""Add test title columns

Revision ID: 1f03af77d718
Revises: 1dd4145ef077
Create Date: 2015-08-15 01:45:02.221610

"""

# revision identifiers, used by Alembic.
revision = '1f03af77d718'
down_revision = '1dd4145ef077'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('TestSuiteResult', sa.Column('title', sa.String, unique=False, nullable=True))
    op.add_column('TestResult', sa.Column('title', sa.String, unique=False, nullable=True))


def downgrade():
    op.drop_column('TestSuiteResult', 'title')
    op.drop_column('TestResult', 'title')
