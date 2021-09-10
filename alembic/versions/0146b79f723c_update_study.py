"""update_study

Revision ID: 0146b79f723c
Revises: 3292cdb4557a
Create Date: 2021-09-06 18:42:12.670422

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# revision identifiers, used by Alembic.


revision = '0146b79f723c'
down_revision = '3292cdb4557a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('study', schema=None) as batch_op:
        batch_op.add_column(sa.Column('path', sa.String(length=255), nullable=True))

    # path data migration
    connexion: Connection = op.get_bind()
    rawstudies = connexion.execute("SELECT id,path FROM rawstudy")
    for rawstudy in rawstudies:
        connexion.execute(text(f"UPDATE study SET path= :path WHERE id='{rawstudy[0]}'"), path=rawstudy[1])
    # end of path data migration

    with op.batch_alter_table('rawstudy', schema=None) as batch_op:
        batch_op.drop_column('path')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rawstudy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('path', sa.VARCHAR(length=255), nullable=True))

    # path data migration
    connexion: Connection = op.get_bind()
    studies = connexion.execute("SELECT id,path FROM study")
    for study in studies:
        connexion.execute(text(f"UPDATE rawstudy SET path=:path WHERE id='{study[0]}'"), path=study[1])
    # end of path data migration

    with op.batch_alter_table('study', schema=None) as batch_op:
        batch_op.drop_column('path')

    # ### end Alembic commands ###
