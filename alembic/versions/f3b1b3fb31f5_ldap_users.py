"""ldap_users

Revision ID: f3b1b3fb31f5
Revises: ab143a39c4db
Create Date: 2021-09-27 17:26:33.599419

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine import Connection

revision = 'f3b1b3fb31f5'
down_revision = 'ab143a39c4db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users_ldap', schema=None) as batch_op:
        batch_op.add_column(sa.Column('external_id', sa.String(), nullable=True))

    # ### end Alembic commands ###
    # data migration
    connexion: Connection = op.get_bind()
    ldap_users = connexion.execute(
        "SELECT users_ldap.id,name,firstname,lastname FROM users_ldap JOIN identities ON identities.id == users_ldap.id")
    for ldap_user in ldap_users:
        connexion.execute(text(f"UPDATE users_ldap SET external_id= :external_id WHERE id='{ldap_user[0]}'"),
                          external_id=ldap_user[1])
        connexion.execute(text(f"UPDATE identities SET name= :name WHERE id='{ldap_user[0]}'"),
                          name=f"{ldap_user[2]} {ldap_user[3]}")
    # end of data migration


def downgrade():
    # data migration
    connexion: Connection = op.get_bind()
    ldap_users = connexion.execute(
        "SELECT id,external_id FROM users_ldap")
    for ldap_user in ldap_users:
        connexion.execute(
            text(f"UPDATE identities SET name= :name WHERE id='{ldap_user[0]}'"), name=ldap_user[1])
    # end of data migration
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users_ldap', schema=None) as batch_op:
        batch_op.drop_column('external_id')

    # ### end Alembic commands ###
