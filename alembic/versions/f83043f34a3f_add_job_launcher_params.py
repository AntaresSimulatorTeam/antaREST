"""add_job_launcher_params

Revision ID: f83043f34a3f
Revises: ef72a8a1c9cf
Create Date: 2022-03-22 17:10:10.888752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f83043f34a3f'
down_revision = 'ef72a8a1c9cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('job_result', schema=None) as batch_op:
        batch_op.add_column(sa.Column('launcher_params', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('job_result', schema=None) as batch_op:
        batch_op.drop_column('launcher_params')

    # ### end Alembic commands ###
