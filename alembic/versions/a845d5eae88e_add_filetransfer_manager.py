"""add_filetransfer_manager

Revision ID: a845d5eae88e
Revises: 9846e90c2868
Create Date: 2021-11-24 14:42:12.269690

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a845d5eae88e'
down_revision = 'dcbe7dbf500b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('file_download',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.Column('ready', sa.Boolean(), nullable=True),
    sa.Column('expiration_date', sa.DateTime(), nullable=True),
    sa.Column('failed', sa.Boolean(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('file_download')
    # ### end Alembic commands ###
