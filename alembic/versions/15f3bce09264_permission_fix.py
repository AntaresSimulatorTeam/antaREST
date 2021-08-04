"""permission_fix

Revision ID: 15f3bce09264
Revises: bb2d1f638a3e
Create Date: 2021-07-29 14:12:36.116348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15f3bce09264'
down_revision = 'bb2d1f638a3e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    if op.get_context().dialect.name == 'sqlite':
        return
    op.execute("GRANT USAGE, SELECT ON SEQUENCE identity_id_seq TO public;")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
