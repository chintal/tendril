"""Add desc to TestResult and TestSuiteResult

Revision ID: 1dd4145ef077
Revises:
Create Date: 2015-08-09 16:43:25.902034

"""

# revision identifiers, used by Alembic.
revision = '1dd4145ef077'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('TestSuiteResult', sa.Column('desc', sa.String, unique=False, nullable=True))
    op.add_column('TestResult', sa.Column('desc', sa.String, unique=False, nullable=True))


def downgrade():
    op.drop_column('TestSuiteResult', 'desc')
    op.drop_column('TestResult', 'desc')
