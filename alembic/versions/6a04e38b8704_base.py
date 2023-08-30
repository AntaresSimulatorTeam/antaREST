"""base

Revision ID: 6a04e38b8704
Revises: 
Create Date: 2021-07-13 15:42:32.381300

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a04e38b8704'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('groups',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('identities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_result',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('study_id', sa.String(length=36), nullable=True),
    sa.Column('launcher', sa.String(), nullable=True),
    sa.Column('job_status', sa.Enum('PENDING', 'FAILED', 'SUCCESS', 'RUNNING', name='jobstatus'), nullable=True),
    sa.Column('creation_date', sa.DateTime(), nullable=True),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.Column('msg', sa.String(), nullable=True),
    sa.Column('output_id', sa.String(), nullable=True),
    sa.Column('exit_code', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('matrix',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('time_step', sa.Enum('HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'ANNUAL', name='matrixfreq'), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('matrix_group',
    sa.Column('matrix_id', sa.String(length=64), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['matrix_id'], ['matrix.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['identities.id'], ),
    sa.PrimaryKeyConstraint('matrix_id', 'owner_id', 'group_id')
    )
    op.create_table('matrix_metadata',
    sa.Column('matrix_id', sa.String(length=64), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['matrix_id'], ['matrix.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['identities.id'], ),
    sa.PrimaryKeyConstraint('matrix_id', 'owner_id', 'key')
    )
    op.create_table('matrix_user_metadata',
    sa.Column('matrix_id', sa.String(length=64), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['matrix_id'], ['matrix.id'], name='fk_matrix_user_metadata_matrix_id'),
    sa.ForeignKeyConstraint(['owner_id'], ['identities.id'], name='fk_matrix_user_metadata_identities_id'),
    sa.PrimaryKeyConstraint('matrix_id', 'owner_id')
    )
    op.create_table('roles',
    sa.Column('type', sa.Enum('ADMIN', 'RUNNER', 'WRITER', 'READER', name='roletype'), nullable=True),
    sa.Column('identity_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ),
    sa.PrimaryKeyConstraint('identity_id', 'group_id')
    )
    op.create_table('study',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('version', sa.String(length=255), nullable=True),
    sa.Column('author', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('public_mode', sa.Enum('NONE', 'READ', 'EXECUTE', 'EDIT', 'FULL', name='publicmode'), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['identities.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('_pwd', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['identities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users_ldap',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['identities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner', sa.Integer(), nullable=True),
    sa.Column('is_author', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['identities.id'], ),
    sa.ForeignKeyConstraint(['owner'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('group_metadata',
    sa.Column('group_id', sa.String(length=36), nullable=True),
    sa.Column('study_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['study_id'], ['study.id'], )
    )
    op.create_table('rawstudy',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('content_status', sa.Enum('VALID', 'WARNING', 'ERROR', name='studycontentstatus'), nullable=True),
    sa.Column('workspace', sa.String(length=255), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['study.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rawstudy')
    op.drop_table('group_metadata')
    op.drop_table('bots')
    op.drop_table('users_ldap')
    op.drop_table('users')
    op.drop_table('study')
    op.drop_table('roles')
    op.drop_table('matrix_user_metadata')
    op.drop_table('matrix_metadata')
    op.drop_table('matrix_group')
    op.drop_table('matrix')
    op.drop_table('job_result')
    op.drop_table('identities')
    op.drop_table('groups')
    # ### end Alembic commands ###

    op.execute("DROP TYPE jobstatus;")
    op.execute("DROP TYPE matrixfreq;")
    op.execute("DROP TYPE publicmode;")
    op.execute("DROP TYPE roletype;")
    op.execute("DROP TYPE studycontentstatus;")

